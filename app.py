import streamlit as st
from PIL import Image
from pathlib import Path
from chat_api_handler import ChatAPIHandler
from streamlit_mic_recorder import mic_recorder
from utils import get_timestamp, load_config, get_avatar
from audio_handler import transcribe_audio
from pdf_handler import add_documents_to_db
from html_templates import css
from database_operations import save_text_message, save_image_message, save_audio_message, load_messages, get_all_chat_history_ids, delete_chat_history, load_last_k_text_messages_ollama
from utils import list_openai_models, list_ollama_models, command
import sqlite3
config = load_config()

# Load and resize the image
logo_long_image = Image.open("assets/logo_long_image.png")
logo_short_image = Image.open("assets/logo_short_image.png")

def sidebar_footer():
    # Display footer text in the sidebar container
    with st.sidebar:
        st.markdown(
            """
            <div style="position: relative; bottom: 0; width: 100%; padding: 5px; text-align: center; font-size: 0.95em; color: #666;">
                Powered By Ollama & OpenAI 🧠
            </div>
            <div style="position: relative; bottom: 0; width: 100%; padding: 0px; text-align: center; font-size: 1em; color: #fff;">
                Made with ❤️‍🔥 By <strong>Abhijit</strong> & Hardik
            </div>
            """,
            unsafe_allow_html=True
        )

def toggle_pdf_chat():
    st.session_state.pdf_chat = True
    clear_cache()

def detoggle_pdf_chat():
    st.session_state.pdf_chat = False

def get_session_key():
    if st.session_state.session_key == "new_session":
        st.session_state.new_session_key = get_timestamp()
        return st.session_state.new_session_key
    return st.session_state.session_key

def delete_chat_session_history():
    delete_chat_history(st.session_state.session_key)
    st.session_state.session_index_tracker = "new_session"

def clear_cache():
    st.cache_resource.clear()

def list_model_options():
    if st.session_state.endpoint_to_use == "ollama":
        ollama_options = list_ollama_models()
        if ollama_options == []:
            #save_text_message(get_session_key(), "assistant", "No models available, please choose one from https://ollama.com/library and pull with /pull <model_name>")
            st.warning("No ollama models available, please choose one from https://ollama.com/library and pull with /pull <model_name>")
        return ollama_options
    elif st.session_state.endpoint_to_use == "openai":
        return list_openai_models()

def update_model_options():
    st.session_state.model_options = list_model_options()

def main():
    # st.title(":rainbow[AllSense.AI] 🤖")
    # st.title("AllSense.AI 🦾")
    # st.markdown('''_Advance :orange[Multimodal Chatbot] for every medium_ 🤖''')
    st.title("Hello Abhijit! 👋 How can I help you today?")
    # st.write("Powered By OpenAI & Ollama")
    st.write(css, unsafe_allow_html=True)

    with st.expander(label="About Me ☺️", expanded=False):
        intro_text = """
            Yo! I’m AllSense, your genius buddy with a sense for EVERYTHING! 📚🎨🎧 \nWhether it's cracking text, decoding images, or vibing with your voice, I’ve got it all covered. \nLet’s turn your ideas into magic—one chat at a time! 🚀😎 \nReady to make sense together?
        """
        st.code(intro_text)

    # Custom CSS for gray background
    st.markdown("""
        <style>
        .gray-column {
            background-color: #f0f0f0;
            color: black;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    # Creating columns
    text_col, image_col, audio_col = st.columns([1, 1, 1])

    # Adding content with custom styling
    with text_col:
        st.markdown('<div class="gray-column">Dive into your PDFs like a pro 📁</div>', unsafe_allow_html=True)

    with image_col:
        st.markdown('<div class="gray-column">Peek into pictures & unlock stories 🔍</div>', unsafe_allow_html=True)

    with audio_col:
        st.markdown('<div class="gray-column">Talk with your voice & vibe out 🎧</div>', unsafe_allow_html=True)
    
    if "db_conn" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
        st.session_state.db_conn = sqlite3.connect(config["chat_sessions_database_path"], check_same_thread=False)
        st.session_state.audio_uploader_key = 0
        st.session_state.pdf_uploader_key = 1
        st.session_state.endpoint_to_use = "ollama"
        st.session_state.model_options = list_model_options()
        st.session_state.model_tracker = None
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None

    st.sidebar.title("Chat History 💬")

    st.markdown("""<style> \
        img[data-testid="stLogo"] { \
            height: 50px; width: auto%; maxWidth: 100%;  } \
        </style>""", unsafe_allow_html=True,)
    st.logo(logo_long_image, icon_image=logo_short_image)

    chat_sessions = ["new_session"] + get_all_chat_history_ids()
    try:
        index = chat_sessions.index(st.session_state.session_index_tracker)
    except ValueError:
        st.session_state.session_index_tracker = "new_session"
        index = chat_sessions.index(st.session_state.session_index_tracker)
        clear_cache()

    st.sidebar.selectbox("Select a chat session 👇", chat_sessions, key="session_key", index=index)
    st.sidebar.button("Delete Chat Session 🗑️", on_click=delete_chat_session_history)


    api_col, model_col = st.sidebar.columns(2)
    api_col.selectbox(label="Select Provider 🛜", options = ["ollama","openai"], key="endpoint_to_use", on_change=update_model_options)
    model_col.selectbox(label="Select a Model 🤖", options = st.session_state.model_options, key="model_to_use")
    pdf_toggle_col, voice_rec_col = st.sidebar.columns(2)
    pdf_toggle_col.toggle("Start PDF Chat", key="pdf_chat", value=False, on_change=clear_cache)
    with voice_rec_col:
        voice_recording=mic_recorder(start_prompt="Record Audio 🎙️",stop_prompt="Stop recording", just_once=True)
    
    chat_container = st.container()
    user_input = st.chat_input("Type your message here", key="user_input")

    st.sidebar.title("Pro Multimodal Features 🤩")
    with st.sidebar.expander("Chat with any Medium ✨", expanded=False):
        uploaded_pdf = st.file_uploader("Upload a PDF to chat 📁", accept_multiple_files=True, 
                                        key=st.session_state.pdf_uploader_key, type=["pdf"], on_change=toggle_pdf_chat)
        uploaded_image = st.file_uploader("Upload an image file 🌌", type=["jpg", "jpeg", "png"], on_change=detoggle_pdf_chat)
        uploaded_audio = st.file_uploader("Upload an audio file 🔉", type=["wav", "mp3", "ogg"], key=st.session_state.audio_uploader_key)


    # st.sidebar.title("Developers 🧑🏻‍💻")
    # with st.sidebar.expander(label="Meet My Developers 😎", expanded=False):
    #     col1, col2 = st.columns([3, 1])  # Adjust column width ratios for better alignment

    #     # Developer 1: Abhijit Mandal
    #     with col1:
    #         st.markdown(":orange[Abhijit Mandal] 🏅")
    #     with col2:
    #         st.markdown("""
    #             <a href="https://www.linkedin.com/in/abhijit-mandal" target="_blank">
    #                 <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="25" style="margin-right: 10px; margin-top: 5px;">
    #             </a>
    #             <a href="https://github.com/abhijit-mandal" target="_blank">
    #                 <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" width="25" style="margin-top: 5px;">
    #             </a>
    #         """, unsafe_allow_html=True)

    #     # Developer 2: Hardik Sharma
    #     with col1:
    #         st.markdown(":red[Hardik Sharma] 🎖️")
    #     with col2:
    #         st.markdown("""
    #             <a href="https://www.linkedin.com/in/hardik-sharma" target="_blank">
    #                 <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="25" style="margin-right: 10px; margin-top: 5px;">
    #             </a>
    #             <a href="https://github.com/hardik-sharma" target="_blank">
    #                 <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" width="25" style="margin-top: 5px;">
    #             </a>
    #         """, unsafe_allow_html=True)


    sidebar_footer()


    if uploaded_pdf:
        with st.spinner("Processing pdf..."):
            add_documents_to_db(uploaded_pdf)
            st.session_state.pdf_uploader_key += 2

    if voice_recording:
        transcribed_audio = transcribe_audio(voice_recording["bytes"])
        print(transcribed_audio)
        #llm_chain = load_chain()
        llm_answer = ChatAPIHandler.chat(user_input = transcribed_audio, 
                                   chat_history=load_last_k_text_messages_ollama(get_session_key(), config["chat_config"]["chat_memory_length"]))
        save_audio_message(get_session_key(), "user", voice_recording["bytes"])
        save_text_message(get_session_key(), "assistant", llm_answer)

    
    if user_input:
        if user_input.startswith("/"):
            response = command(user_input)
            save_text_message(get_session_key(), "user", user_input)
            save_text_message(get_session_key(), "assistant", response)
            user_input = None

        if uploaded_image:
            with st.spinner("Processing image..."):
                llm_answer = ChatAPIHandler.chat(user_input = user_input, chat_history = [], image = uploaded_image.getvalue())
                save_text_message(get_session_key(), "user", user_input)
                save_image_message(get_session_key(), "user", uploaded_image.getvalue())
                save_text_message(get_session_key(), "assistant", llm_answer)
                user_input = None

        if uploaded_audio:
            transcribed_audio = transcribe_audio(uploaded_audio.getvalue())
            print(transcribed_audio)
            llm_answer = ChatAPIHandler.chat(user_input = user_input + "\n" + transcribed_audio, chat_history=[])
            save_text_message(get_session_key(), "user", user_input)
            save_audio_message(get_session_key(), "user", uploaded_audio.getvalue())
            save_text_message(get_session_key(), "assistant", llm_answer)
            st.session_state.audio_uploader_key += 2
            user_input = None

        if user_input:
            llm_answer = ChatAPIHandler.chat(user_input = user_input, 
                                       chat_history=load_last_k_text_messages_ollama(get_session_key(), config["chat_config"]["chat_memory_length"]))
            save_text_message(get_session_key(), "user", user_input)
            save_text_message(get_session_key(), "assistant", llm_answer)
            user_input = None


    if (st.session_state.session_key != "new_session") != (st.session_state.new_session_key != None):
        with chat_container:
            chat_history_messages = load_messages(get_session_key())

            for message in chat_history_messages:
                with st.chat_message(name=message["sender_type"], avatar=get_avatar(message["sender_type"])):
                    if message["message_type"] == "text":
                        st.write(message["content"])
                    if message["message_type"] == "image":
                        st.image(message["content"])
                    if message["message_type"] == "audio":
                        st.audio(message["content"], format="audio/wav")

        if (st.session_state.session_key == "new_session") and (st.session_state.new_session_key != None):
            st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="AllSense.AI", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
    main()