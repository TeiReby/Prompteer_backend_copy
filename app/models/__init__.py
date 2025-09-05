# app/models/__init__.py
from app.models.relations import *
from app.models.serializers import *

# Pydantic 모델 순환 참조 해결
UserReadWithProfile.model_rebuild()
ChallengeRead.model_rebuild()
PSChallengeReadWithDetails.model_rebuild()
ImgChallengeReadWithDetails.model_rebuild()
VideoChallengeReadWithDetails.model_rebuild()
PostRead.model_rebuild()
CommentRead.model_rebuild()
ShareRead.model_rebuild()
ShareReadWithDetails.model_rebuild()
PSShareReadWithDetails.model_rebuild()
ImgShareReadWithDetails.model_rebuild()
VideoShareReadWithDetails.model_rebuild()
