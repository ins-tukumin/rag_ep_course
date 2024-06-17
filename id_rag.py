import os
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# テンプレートの設定
template = """
    Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question(なお、日本語で答えてください。):
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
st.title("RAG Chatbot with Student ID")
student_id = st.text_input("Enter your student ID:")

with st.sidebar:
    #user_api_key = st.text_input(
        #label="OpenAI API key",
        #placeholder="Paste your OpenAI API key",
        #type="password"
    #)
    #os.environ['OPENAI_API_KEY'] = user_api_key
    select_model = st.selectbox("Model", ["gpt-4", "gpt-4o"])
    select_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.0, step=0.1)

if student_id:
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

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt_input = st.chat_input("Ask something about the file.")

        if prompt_input:
            st.session_state.messages.append({"role": "user", "content": prompt_input})
            with st.chat_message("user"):
                st.markdown(prompt_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chain({"question": prompt_input})
                    st.markdown(response["answer"])
            
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})

    else:
        st.error(f"No vector database found for student ID {student_id}.")
