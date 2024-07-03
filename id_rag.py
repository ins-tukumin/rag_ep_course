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
    この会話では私のお悩み相談に乗ってほしいです。悩みは進路関係に関するものです。
    必要に応じて、私の日記に書かれている情報を参照して、私の事を理解して会話してください。
    ただ、”あなたの日記を読んでみると”といったような、日記を読んだ動作を直接示すような言葉は出力に含めないでください。
    さらに、この会話では私の日記に含まれる「エピソード記憶」を積極的に話題に出して会話してほしいです。エピソード記憶という言葉の意味は以下に示します。
    # エピソード記憶とは、人間の記憶の中でも特に個人的な経験や出来事を覚える記憶の種類の一つです。エピソード記憶は、特定の時間と場所に関連する出来事を含む記憶であり、過去の個人的な経験を詳細に思い出すことができる記憶を指します。
    エピソード記憶を参照して話題に出すというのは、例えば、「あの日に遊園地に行ったときに乗ったあのアトラクションで感じたあの感情は今の感情に似ているね」といった具合です。
    敬語は使わないでください。私の友達になったつもりで砕けた口調で話してください。
    150~200字程度で話してください。
    日本語で話してください。
    Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question. :
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

if student_id:
    if not firebase_admin._apps:
        private_key = st.secrets["private_key"].replace('\\n', '\n')
        cred = credentials.Certificate({
              "type": "service_account",
              "project_id": "rag-ep-course",
              "private_key_id": "9ccd17ed215efabe4969d546a1e784763fae5f36",
              "private_key": private_key,
              "client_email": "firebase-adminsdk-610au@rag-ep-course.iam.gserviceaccount.com",
              "client_id": "115635233497515207535",
              "auth_uri": "https://accounts.google.com/o/oauth2/auth",
              "token_uri": "https://oauth2.googleapis.com/token",
              "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
              "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-610au%40rag-ep-course.iam.gserviceaccount.com",
              "universe_domain": "googleapis.com"
        }) 
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
            if st.session_state.count >= 5:
                html_link = '<a href="https://nagoyapsychology.qualtrics.com/jfe/form/SV_eEVBQ7a0d8iVvq6" target="_blank">これで会話は終了です。こちらをクリックしてアンケートに回答してください。</a>'
                st.markdown(html_link, unsafe_allow_html=True)
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
