import os
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# OpenAI APIキーを設定


# PDFが格納されているディレクトリ
pdf_directory = "./pdfsvector"

# ベクトルデータベースを保存するディレクトリ
db_directory = "./vector_databases"

# 各PDFファイルに対してベクトルデータベースを作成
for pdf_file in os.listdir(pdf_directory):
    if pdf_file.endswith(".pdf"):
        student_id = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(pdf_directory, pdf_file)
        
        loader = PyMuPDFLoader(file_path=pdf_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=100,
            length_function=len,
        )

        data = text_splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
        )

        student_db_dir = os.path.join(db_directory, student_id)
        if not os.path.exists(student_db_dir):
            os.makedirs(student_db_dir)

        database = Chroma(
            persist_directory=student_db_dir,
            embedding_function=embeddings,
        )

        database.add_documents(data)

print("Vector databases created successfully.")
