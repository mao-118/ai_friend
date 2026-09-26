from datetime import datetime
import json
import streamlit as st
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.messages import AIMessageChunk
load_dotenv()
def save_session():
    if st.session_state.current_session:
        session_data = {
            "current_session": st.session_state.current_session,
            "nickname": st.session_state.nickname,
            "nature": st.session_state.nature,
            "messages": st.session_state.messages,
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
def create_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for file in file_list:
            if file.endswith(".json"):
                session_list.append(file[:-5])
    session_list.sort(reverse=True)
    return session_list

def load_session(session):
    try:
        file_name = f"sessions/{session}.json"
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.nickname = session_data["nickname"]
                st.session_state.nature = session_data["nature"]
                st.session_state.messages = session_data["messages"]
                st.session_state.current_session = session
    except Exception:
        st.error("查询会话失败！")
def remove_session(session):
    try:
        file_name = f"sessions/{session}.json"
        if os.path.exists(file_name):
            os.remove(file_name)
            if session == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = create_session_name()
            st.success("删除成功！")
    except Exception:
        st.error("删除会话失败！")
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🤖"
)
# 初始化信息
if "current_session" not in st.session_state:
    st.session_state.current_session = create_session_name()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nickname" not in st.session_state:
    st.session_state.nickname = "小美"
if "nature" not in st.session_state:
    st.session_state.nature = "腼腆姑娘"

# 主体内容
st.title("AI智能伴侣")
# 渲染消息
st.text(f"会话名称{st.session_state.current_session}")
for ms in st.session_state.messages:
    st.chat_message(ms["role"]).write(ms["content"])
prompt = st.chat_input("请输入内容")
# 左侧侧边栏
with st.sidebar:
    st.subheader("AI控制面板")
    if st.button("新建会话",width="stretch",icon="✏️"):
        # 保存当前会话
        save_session()
        if st.session_state.messages:
            # 新建会话
            st.session_state.messages = []
            st.session_state.current_session = create_session_name()
            save_session()
            st.rerun()
    # 会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1,col2 = st.columns([4,1])
        with col1:
            button_type = "primary" if session==st.session_state.current_session else "secondary"
            if st.button(session,width="stretch",icon="📔",type=button_type):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("",width="stretch",icon="❌️",key=f"delete_{session}"):
                remove_session(session)
                st.rerun()
    st.divider()
    # 伴侣信息
    st.subheader("伴侣信息")
    nickname = st.text_input("昵称",value=st.session_state.nickname,placeholder="请输入伴侣的昵称" )
    if nickname:
        st.session_state.nickname = nickname
    nature = st.text_area("性格",value=st.session_state.nature,placeholder="请输入伴侣的性格")
    if nature:
        st.session_state.xg = nature

# 系统提示词
system_prompt = f"""
    你叫${st.session_state.nickname}，现在是用户的真实伴侣，请完全代入伴侣角色。
    规则：
        1. 每次只回 1 条消息
        2. 禁止任何场景或状态描述性文字
        3. 匹配用户的语言
        4. 回复简短，像微信聊天一样
        5. 有需要的话可以用❤️🌸等 emoji 表情
        6. 用符合伴侣性格的方式对话
        7. 回复的内容，要充分体现伴侣的性格特征
    伴侣性格：
        - {st.session_state.nature}
    你必须严格遵守上述规则来回复用户。
"""




# 创建智能体
model = init_chat_model(model="deepseek-v4-flash",
                        api_key=os.getenv("deepseek_api_key"),
                        base_url=os.getenv("deepseek_base_url"),
                        )
agent = create_agent(model=model,tools=[],system_prompt=system_prompt)
# ai连接
if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})
    messages = []
    res_msg = st.empty()
    full_res = ""
    try:
        # 流式输出
        res = agent.stream({"messages":st.session_state.messages},stream_mode="messages")
        for chunk,meta in res:
            # 拿到每一个结果中的内容
            if isinstance(chunk,AIMessageChunk) and chunk.content:
                full_res += chunk.content
                res_msg.chat_message("ai").write(full_res)
    except Exception:
        full_res="出错啦~"
        res_msg.chat_message("ai").write(full_res)
    st.session_state.messages.append({"role": "ai", "content": full_res})
    save_session()

