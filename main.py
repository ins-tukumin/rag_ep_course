import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain.callbacks import get_openai_callback
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import pytz
global now
now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))

def init_page():
    st.set_page_config(
        page_title="にゃんぱす　ちゃっと　ぼっと",
        page_icon="🤗"
    )
    st.header("にゃんぱす　ちゃっと　ぼっと 🤗")
    st.sidebar.title("Options")


def init_messages():
    clear_button = st.sidebar.button("Clear Conversation", key="clear")
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="語尾に'にゃん'をつけて可愛く返答してください")
        ]
        st.session_state.costs = []


def select_model():
    model = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
    if model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
    else:
        model_name = "gpt-4"

    # スライダーを追加し、temperatureを0から2までの範囲で選択可能にする
    # 初期値は0.0、刻み幅は0.01とする
    temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=2.0, value=0.0, step=0.01)

    return ChatOpenAI(temperature=temperature, model_name=model_name)


def get_answer(llm, messages):
    with get_openai_callback() as cb:
        answer = llm(messages)
    return answer.content, cb.total_cost


def main():
    init_page()

    llm = select_model()
    init_messages()
    count = 0
    if not firebase_admin._apps:
        # 初期済みでない場合は初期化処理を行う
        cred = credentials.Certificate('chatapp-509c9-firebase-adminsdk-5tvj9-9106d52707.json') 
        default_app = firebase_admin.initialize_app(cred)

    db = firestore.client()
    doc_ref = db.collection(u'chattest').document(str(now))


    # ユーザーの入力を監視
    if user_input := st.chat_input("聞きたいことを入力してね！"):
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.spinner("にゃんぱすなう。。。"):
            answer, cost = get_answer(llm, st.session_state.messages)
        st.session_state.messages.append(AIMessage(content=answer))
        st.session_state.costs.append(cost)
        a_count = "Human" + str(count)
        b_count = "AI" + str(count)
        # firestoreデータベースへの書き込み
        doc_ref.set({
            a_count: user_input,
            b_count: answer
        })

    messages = st.session_state.get('messages', [])
    for message in messages:
        if isinstance(message, AIMessage):
            with st.chat_message('assistant'):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message('user'):
                st.markdown(message.content)
        else:  # isinstance(message, SystemMessage):
            st.write(f"System message: {message.content}")

    costs = st.session_state.get('costs', [])
    st.sidebar.markdown("## Costs")
    st.sidebar.markdown(f"**Total cost: ${sum(costs):.5f}**")
    for cost in costs:
        st.sidebar.markdown(f"- ${cost:.5f}")

if __name__ == '__main__':
    main()