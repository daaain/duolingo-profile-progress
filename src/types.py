"""Type definitions for Duolingo API responses"""

from typing import TypedDict, Any, Union


class DuolingoCourse(TypedDict):
    """Represents a Duolingo course/language"""

    preload: bool
    placementTestAvailable: bool
    authorId: str
    title: str
    learningLanguage: str
    xp: int
    healthEnabled: bool
    fromLanguage: str
    crowns: int
    id: str


class DuolingoCurrentStreak(TypedDict, total=False):
    """Current streak data - can be null"""

    length: int


class DuolingoStreakData(TypedDict):
    """Streak information"""

    currentStreak: DuolingoCurrentStreak | None


class DuolingoGlobalAmbassadorStatus(TypedDict):
    """Global ambassador status - appears to be empty dict"""

    pass


class DuolingoUser(TypedDict):
    """Represents a Duolingo user from the API"""

    joinedClassroomIds: list[str]
    streak: int
    motivation: str
    acquisitionSurveyReason: str
    shouldForceConnectPhoneNumber: bool
    picture: str
    learningLanguage: str
    hasFacebookId: bool
    shakeToReportEnabled: bool | None
    liveOpsFeatures: list[Any]
    canUseModerationTools: bool
    id: int
    betaStatus: str
    hasGoogleId: bool
    privacySettings: list[Any]
    fromLanguage: str
    hasRecentActivity15: bool
    _achievements: list[Any]
    location: str
    observedClassroomIds: list[str]
    username: str
    bio: str
    profileCountry: str | None
    chinaUserModerationRecords: list[Any]
    globalAmbassadorStatus: DuolingoGlobalAmbassadorStatus
    currentCourseId: str
    hasPhoneNumber: bool
    creationDate: int
    achievements: list[Any]
    hasPlus: bool
    name: str
    roles: list[str]
    classroomLeaderboardsEnabled: bool
    emailVerified: bool
    courses: list[DuolingoCourse]
    totalXp: int
    streakData: DuolingoStreakData


class DuolingoApiResponse(TypedDict):
    """Root response from Duolingo API"""

    users: list[DuolingoUser]


class LanguageProgress(TypedDict):
    """Internal representation of language progress"""

    level: int
    xp: int
    from_language: str
    learning_language: str


class UserProgress(TypedDict):
    """Internal representation of user progress"""

    username: str
    name: str
    streak: int
    total_xp: int
    weekly_xp: int
    weekly_xp_per_language: dict[str, int]
    total_languages_xp: int
    active_languages: list[str]
    language_progress: dict[str, LanguageProgress]
    last_check: str


class UserProgressError(TypedDict):
    """User progress with error"""

    username: str
    error: str
    last_check: str
    language_progress: dict[str, LanguageProgress]
    weekly_xp_per_language: dict[str, int]
    active_languages: list[str]


class HistoryEntry(TypedDict):
    """Historical data entry"""

    date: str
    results: dict[str, Union[UserProgress, UserProgressError]]
