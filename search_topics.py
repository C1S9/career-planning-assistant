"""Translate coaching concerns into public topics without exporting private text."""

from collections.abc import Sequence

from mentors import get_mentor


# Only these fixed phrases can enter a search query. Names, contact details,
# employers, exact ages, and other free-form conversation text never enter it.
TOPICS = {
    "career": (
        ("career change transferable skills", ("career change", "retail", "transferable", "转行", "转岗", "零售")),
        ("job interview preparation", ("interview", "面试")),
        ("job search resume skills", ("resume", "cv", "job search", "简历", "求职", "就业")),
        ("career planning skills assessment", ()),
    ),
    "direction": (
        ("career decision making values", ("career", "work", "job", "职业", "工作", "就业")),
        ("wellbeing values decision making", ()),
    ),
    "learning": (
        ("learning programming practice", ("python", "coding", "programming", "编程")),
        ("learning spaced practice retrieval", ("exam", "memory", "remember", "考试", "记忆")),
        ("adult learning study skills", ()),
    ),
    "habits": (
        ("sleep healthy routines", ("sleep", "insomnia", "睡眠", "失眠")),
        ("physical activity daily habits", ("exercise", "fitness", "运动", "健身")),
        ("stress manageable goals routines", ()),
    ),
    "relationships": (
        ("workplace communication conflict", ("boss", "colleague", "manager", "workplace", "同事", "老板", "职场")),
        ("healthy relationships communication boundaries", ()),
    ),
}

REGIONS = ("Not specified", "China", "United States", "United Kingdom", "Canada", "Australia")
CHINA_TOPICS = {
    "career change transferable skills": "职业转换 可迁移技能",
    "job interview preparation": "求职 面试准备",
    "job search resume skills": "求职 简历 技能",
    "career planning skills assessment": "职业规划 技能评估",
    "career decision making values": "职业选择 决策",
    "wellbeing values decision making": "心理健康 生活目标",
    "learning programming practice": "学习 编程 实践",
    "learning spaced practice retrieval": "学习 记忆 方法",
    "adult learning study skills": "成人学习 学习方法",
    "sleep healthy routines": "睡眠 健康习惯",
    "physical activity daily habits": "运动 健康习惯",
    "stress manageable goals routines": "心理压力 目标 习惯",
    "workplace communication conflict": "职场 沟通 冲突",
    "healthy relationships communication boundaries": "人际关系 沟通",
}


def search_topic(messages: Sequence[dict], mentor_id: str, region: str = "Not specified") -> str:
    """Use the latest recognized concern, keeping the search vocabulary finite."""
    get_mentor(mentor_id)
    if region not in REGIONS:
        raise ValueError("Choose a supported source region.")
    options = TOPICS[mentor_id]
    topic = options[-1][0]
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content", "").casefold()
        matched = next((phrase for phrase, words in options[:-1] if any(word in content for word in words)), None)
        if matched:
            topic = matched
            break
    # Region is an explicit selection, never inferred from language or identity.
    if region == "China":
        return CHINA_TOPICS[topic] + " 中国"
    return topic if region == "Not specified" else f"{topic} {region}"
