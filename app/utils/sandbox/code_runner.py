# app/utils/sandbox/code_runner.py
import asyncio
import os
import re
import tempfile
import time

# =================================================================
# 코드 실행 샌드박스 설정
# =================================================================
# 이 스크립트는 외부에서 제출된 파이썬 코드를 안전한 환경에서 실행하기 위한
# 샌드박스(격리 환경) 기능을 제공합니다. Docker를 사용하여 각 코드를
# 독립된 컨테이너에서 실행함으로써 시스템에 영향을 주지 않도록 보장합니다.

# --- 설정값: 코드 실행 환경을 제어하는 주요 변수들 ---
DOCKER_IMAGE = "python-with-time"  # 코드 실행에 사용할 Docker 이미지 이름
DEFAULT_TIMEOUT_SECONDS = 10  # 기본 코드 실행 최대 시간 (초)
DEFAULT_MEMORY_LIMIT_MB = 128  # 기본 최대 메모리 (MB)
CPU_LIMIT = "0.5"  # 컨테이너가 사용할 수 있는 CPU 코어 수 (0.5는 절반)

async def score_code(
    code: str,
    stdin_data: str = "",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
) -> dict:
    """
    주어진 Python 코드를 격리된 Docker 컨테이너 내에서 실행하고, 그 결과를 상세히 반환합니다.

    이 함수는 비동기적으로 작동하며, 다음과 같은 주요 단계를 거칩니다:
    1. 임시 디렉토리를 생성하고 제출된 코드를 'client_script.py' 파일로 저장합니다.
    2. Docker 컨테이너를 실행하여 이 스크립트를 실행합니다. 이때 네트워크, 메모리, CPU 사용량을 제한합니다.
    3. '/usr/bin/time -v' 명령어를 사용하여 코드 실행 시간과 메모리 사용량을 측정하고, 각 출력을 별도 파일에 저장합니다.
    4. 실행 완료 후, 생성된 파일들을 읽어 성공 여부, 표준 출력(stdout), 표준 에러(stderr), 실행 시간, 메모리 사용량 등을
       포함한 딕셔너리 형태로 반환합니다.
    5. 타임아웃, 메모리 초과 등 다양한 예외 상황을 처리합니다.

    Args:
        code (str): 실행할 Python 코드.
        stdin_data (str, optional): 코드 실행 시 표준 입력으로 전달할 데이터.
        timeout_seconds (float, optional): 코드 실행 시간 제한 (초).
        memory_limit_mb (int, optional): 최대 메모리 사용량 제한 (MB).

    Returns:
        dict: 실행 결과를 담은 딕셔너리.
              (예: {"success": True, "stdout": "Hello", "stderr": "", ...})
    """
    # 임시 디렉토리를 사용하여 스크립트 및 결과 파일을 안전하게 관리합니다.
    # `with` 블록이 끝나면 디렉토리와 그 안의 모든 파일은 자동으로 삭제됩니다.
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = os.path.join(temp_dir, "client_script.py")
        stdout_path = os.path.join(temp_dir, "stdout.txt")
        stderr_path = os.path.join(temp_dir, "stderr.txt")
        time_stats_path = os.path.join(temp_dir, "time_stats.txt")

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 컨테이너 내부에서 실행될 쉘 명령을 구성합니다.
        # `/usr/bin/time -v`: 프로세스의 상세한 리소스 사용량(메모리, 시간 등)을 측정합니다.
        # `-o {time_stats_path}`: 측정 결과를 지정된 파일에 저장합니다.
        # `> {stdout_path} 2> {stderr_path}`: 표준 출력과 표준 에러를 각각 다른 파일로 리디렉션합니다.
        shell_command = (
            f"/usr/bin/time -v -o {time_stats_path} "
            f"python client_script.py > {stdout_path} 2> {stderr_path}"
        )

        # Docker 컨테이너 실행을 위한 명령어 리스트를 구성합니다.
        command = [
            "docker", "run",
            "--rm",  # 컨테이너 실행 종료 시 자동으로 컨테이너 삭제
            "-i",  # 컨테이너의 표준 입력(stdin)을 활성화
            "--network", "none",  # 네트워크 접근을 차단하여 외부 통신 방지
            "--memory", f"{memory_limit_mb}m",  # 메모리 사용량 제한
            "--cpus", CPU_LIMIT,  # CPU 사용량 제한
            "-v", f"{temp_dir}:{temp_dir}",  # 호스트의 임시 디렉토리를 컨테이너에 마운트
            "-w", temp_dir,  # 컨테이너의 작업 디렉토리를 마운트된 디렉토리로 설정
            DOCKER_IMAGE,  # 사용할 Docker 이미지
            "bash", "-c", shell_command  # 컨테이너에서 실행할 최종 명령어
        ]

        start_time = time.monotonic()
        try:
            # 비동기적으로 외부 프로세스(Docker)를 실행합니다.
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 표준 입력을 전달하고, 지정된 시간 내에 프로세스가 완료되기를 기다립니다.
            await asyncio.wait_for(
                process.communicate(input=stdin_data.encode("utf-8")),
                timeout=timeout_seconds
            )

            elapsed_time = time.monotonic() - start_time

            # 실행 결과가 저장된 파일들을 읽어옵니다.
            user_stdout = open(stdout_path, "r", encoding="utf-8").read()
            user_stderr = open(stderr_path, "r", encoding="utf-8").read()
            time_stats = open(time_stats_path, "r", encoding="utf-8").read()

            # 정규 표현식을 사용하여 `time` 명령어의 출력에서 최대 메모리 사용량(KB)을 추출합니다.
            mem_match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", time_stats)
            max_memory_kb = int(mem_match.group(1)) if mem_match else None

            is_success = False
            error_type = None

            # 프로세스의 종료 코드를 기반으로 성공/실패 및 에러 유형을 판단합니다.
            if process.returncode == 0:
                is_success = True
            elif process.returncode == 137:  # OOM Killer에 의해 종료된 경우 (메모리 초과)
                error_type = "Memory Limit Exceeded"
                if not user_stderr:
                    user_stderr = "메모리 제한을 초과하여 프로세스가 종료되었습니다."
            else:
                # stderr 내용을 분석하여 컴파일 에러와 런타임 에러를 구분합니다.
                if "SyntaxError:" in user_stderr or "IndentationError:" in user_stderr:
                    error_type = "Compilation Error"
                else:
                    error_type = "Runtime Error"

            return {
                "success": is_success,
                "stdout": user_stdout,
                "stderr": user_stderr,
                "max_memory_kb": max_memory_kb,
                "elapsed_time": elapsed_time,
                "error": error_type,
            }

        except asyncio.TimeoutError:
            # `asyncio.wait_for`에서 설정한 시간을 초과한 경우
            elapsed_time = time.monotonic() - start_time
            return {
                "success": False, "stdout": "", "stderr": f"실행 시간이 {timeout_seconds}초를 초과했습니다.",
                "max_memory_kb": None, "elapsed_time": elapsed_time, "error": "Timeout",
            }
        except FileNotFoundError:
            # Docker가 설치되지 않았거나 경로에 없는 경우
            if not os.path.exists("/var/run/docker.sock"):
                 return {
                    "success": False, "stdout": "", "stderr": "", "max_memory_kb": None,
                    "elapsed_time": 0, "error": "Docker 명령어를 찾을 수 없습니다. Docker가 설치되어 있고 실행 중인지 확인하세요."
                }

            # 프로세스가 비정상적으로 종료되어 결과 파일이 생성되지 않은 경우
            elapsed_time = time.monotonic() - start_time
            user_stderr = ""
            if os.path.exists(stderr_path):
                user_stderr = open(stderr_path, "r", encoding="utf-8").read()

            return {
                "success": False, "stdout": "", "stderr": user_stderr, "max_memory_kb": None,
                "elapsed_time": elapsed_time, "error": "Runtime Error",
            }
        except Exception as e:
            # 그 외 예상치 못한 모든 예외를 처리합니다.
            elapsed_time = time.monotonic() - start_time
            return {
                "success": False, "stdout": "", "stderr": str(e), "max_memory_kb": None,
                "elapsed_time": elapsed_time, "error": "예상치 못한 오류가 발생했습니다.",
            }

