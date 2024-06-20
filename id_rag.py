import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
import streamlit as st
from streamlit_chat import message
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import pytz
import time

#現在時刻
global now
now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))

# テンプレートの設定
template = """
    私の日記情報を添付します。
    この日記を読んで、私の事をよく理解した上で会話してください。
    そして、私の相談に乗って少しでも私の気持ちを楽にしてほしいです。
    表面的なコミュニケーションではなく、私のことをよく理解した上で会話してほしいです。
    受け身にならずに積極的に私に語り掛けてほしいです。
    敬語は使わないでください。私の友達になったつもりで砕けた口調で話してください。
    150~200字程度で話してください。
    日本語で話してください。
    Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question. また、ドキュメントを提供しますので、適宜参照して会話してください。なお、日本語で話してください。:
    ------
    <ctx>
    {context}
    </ctx>
    ------
    <hs>
    {chat_history}
    </hs>
    ------
    {question}
    Answer:
    """

# 会話のテンプレートを作成
prompt = PromptTemplate(
    input_variables=["chat_history", "context", "question"],
    template=template,
)

# UIの設定
student_id = st.text_input("学籍番号を半角で入力してエンターを押してください")

#with st.sidebar:
    #user_api_key = st.text_input(
        #label="OpenAI API key",
        #placeholder="Paste your OpenAI API key",
        #type="password"
    #)
    #os.environ['OPENAI_API_KEY'] = user_api_key
select_model = "gpt-4o"
select_temperature = 0.0

if student_id:
    if not firebase_admin._apps:
        cred = credentials.Certificate('ragtest-5e402-firebase-adminsdk-qz4o3-ce2b4f2ed6.json') 
        default_app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    db_path = f"./vector_databases/{student_id}"
    if os.path.exists(db_path):
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
        )

        database = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings,  # エンベディング関数を提供
        )

        chat = ChatOpenAI(
            model=select_model,
            temperature=select_temperature,
        )

        retriever = database.as_retriever()

        if "memory" not in st.session_state:
            st.session_state.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
            )

        memory = st.session_state.memory

        chain = ConversationalRetrievalChain.from_llm(
            llm=chat,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={'prompt': prompt}
        )

        #--------------------------------------------
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "generated" not in st.session_state:
            st.session_state.generated = []
        if "past" not in st.session_state:
            st.session_state.past = []
        if "count" not in st.session_state:
            st.session_state.count = 0

        def on_input_change():
            st.session_state.count += 1
            user_message = st.session_state.user_message
            with st.spinner("Thinking..."):
                response = chain({"question": user_message})
                response_text = response["answer"]
            st.session_state.past.append(user_message)
            st.session_state.generated.append(response_text)
            st.session_state.user_message = ""
            #st.session_state["user_message"] = ""
            Human_Agent = "Human" 
            AI_Agent = "AI" 
            doc_ref = db.collection(student_id).document(str(now))
            doc_ref.set({
                Human_Agent: user_message,
                AI_Agent: response_text
            })
        # 会話履歴を表示するためのスペースを確保
        chat_placeholder = st.empty()
        # 会話履歴を表示
        with chat_placeholder.container():
            for i in range(len(st.session_state.generated)):
                message(st.session_state.past[i], is_user=True, key=str(i), avatar_style="adventurer", seed="Nala")
                key_generated = str(i) + "keyg"
                message(st.session_state.generated[i], key=str(key_generated), avatar_style="micah")
                
        with st.container():
            if st.session_state.count == 3:
                st.write("3 turns completed. Please proceed to the next step.")
            else:
                user_message = st.text_input("内容を入力して送信ボタンを押してください", key="user_message")
                st.button("送信", on_click=on_input_change)
        # ターン数に応じた機能を追加
        #--------------------------------------------
        #if "messages" not in st.session_state:
            #st.session_state.messages = []

        #for message in st.session_state.messages:
           # with st.chat_message(message["role"]):
                #st.markdown(message["content"])

        #prompt_input = st.chat_input("入力してください", key="propmt_input")

        #if prompt_input:
            #st.session_state.messages.append({"role": "user", "content": prompt_input})
            #with st.chat_message("user"):
                #st.markdown(prompt_input)

            #with st.chat_message("assistant"):
                #with st.spinner("Thinking..."):
                    #response = chain({"question": prompt_input})
                    #st.markdown(response["answer"])
            
            #st.session_state.messages.append({"role": "assistant", "content": response["answer"]})

    else:
        st.error(f"No vector database found for student ID {student_id}.")


hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
