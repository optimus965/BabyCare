import openai
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import docx  #pip install python-docx

from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks import get_openai_callback
import os

from telegram.ext import *
import random
import io
from telegram import InputFile
from datetime import datetime
import pytz

load_dotenv()
print('loaded env')
quotes=['A baby fills a place in your heart that you never knew was empty.',
        "A mother's love is a guiding light in a child's life.",
        "In a mother's arms, a baby finds endless love.",
        "A baby's smile is the reflection of a mother's love.",
        ]
greetings=["Hello there! I'm Meera, your dedicated guide through the magical world of motherhood. How may I be of assistance today?",
           "Hi there! I'm Meera, your go-to resource for all things related to taking care of your precious little one.Let's navigate this journey together!"
           
           ]


data=''' '''
IST = pytz.timezone('Asia/Kolkata')
time=str(datetime.now(IST))[11:19]
bot_key='6230020710:AAHGdnDczi4UNXgwepiJfw5zE25GDctiuB4'
updater=Updater(bot_key,use_context=True)
bot=updater.bot
conversation_timeout=600
#os.environ['OPENAI_API_KEY']='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'

try:
  file_path='text_chunks.txt'
  if os.path.exists(file_path):
                print('yes')
  retrive_code='vishnu1$'
  with open(file_path,'r') as f:
    text_chunks=f.read().split(retrive_code)
  tokens=400
  print(len(text_chunks))
  
  print('Loading Embedding model ...')
  embeddings_model_name1='all-MiniLM-L6-v2'
  embeddings_model_name2='distilbert-base-nli-stsb-mean-tokens'
  embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name1)
  print('Creating docsearch ...')
  
  try:
    docsearch = FAISS.from_texts(text_chunks, embeddings)
  except Exception as e:
    print('error in docsearch...')
    print(e)
  print('Loading LLM model ...')
  llm = ChatOpenAI(temperature=0.5,model_name='gpt-3.5-turbo',max_tokens=tokens)
  chain = load_qa_chain(llm, chain_type="stuff")
except Exception as e:
  print('error in loading ....')
  print(e)
START,QUERY,FBACK=range(3)
def cancel(update,context):
  if len(context.user_data['data'])!=0:
    file_data=io.BufferedReader(io.BytesIO(context.user_data['data'].encode('UTF-8')))
    file_data=InputFile(file_data,f'feedback {str(update.message.chat_id)}-{time}.txt')
    bot.send_document(1151232298,file_data)
  return ConversationHandler.END
def start(update,context):
  
  context.user_data['data']=''
  greet=random.choice(greetings)
  update.message.reply_text(f'{greet}')
  return QUERY
def query(update,context):
  query=update.message.text
  context.user_data['query']=query
  update.message.reply_text('Please wait generating your response .....')
  docs = docsearch.similarity_search(query)
  with get_openai_callback() as cb:
    response = chain.run(input_documents=docs, question=query )
    context.user_data['cb']=str(cb)
  update.message.reply_text(str(response ))#+'  '+str(cb)))
  context.user_data['response']=response
  
  update.message.reply_text(''' Is the generated content meeting your expectations? (y/n/c)

        c -> can be improved !
  ''')
  
  return FBACK
def fback(update,context):
  query=context.user_data['query']
  content=context.user_data['response']
  feed_back=update.message.text
  data=context.user_data['data']
  cb=context.user_data['cb']
  fb=['y','n','c']
  if feed_back.lower() not in fb:
    update.message.reply_text('Please enter a valid feed  back (y/n/c)...')
    return FBACK
  else:
    context.user_data['data']=context.user_data['data']+'\n'+query+'\n\n'+content+'\n\n'+feed_back.upper()+'\n\n'+str(cb)+'\n'+'--------------------------------------------'+'\n'
    data+=context.user_data['data']
    update.message.reply_text('Thank you for your FeedBack !')
    return QUERY
def main():
  print('Bot has started .....')
  dp=updater.dispatcher
  start_handler=ConversationHandler(
      entry_points=[CommandHandler('start',start)],
      states={
          START:[MessageHandler(Filters.text & (~ Filters.command) ,start)],
          QUERY:[MessageHandler(Filters.text & (~ Filters.command),query)],
          FBACK:[MessageHandler(Filters.text & (~ Filters.command),fback)]
          
      },
      fallbacks=[MessageHandler(Filters.command,cancel)],
      allow_reentry=True,
      conversation_timeout=conversation_timeout
  )
  dp.add_handler(start_handler,1)
  updater.start_polling()
  updater.idle()
try:
  main()
except:
  if len(data)!=0:
    file_data=io.BufferedReader(io.BytesIO(data.encode('UTF-8')))
    file_data=InputFile(file_data,f'feedback error-{time}.txt')
    bot.send_document(1151232298,file_data)
