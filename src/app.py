import gradio as gr
from utils.chatbot import ChatBot
from utils.ui_settings import UISettings


with gr.Blocks() as demo:
    with gr.Tabs():
        with gr.TabItem("Q&A-with-SQL-and-TabularData"):
            ##############
            # First ROW:
            ##############
            with gr.Row() as row_one:
                chatbot = gr.Chatbot(
                    [],
                    elem_id="chatbot",
                    bubble_full_width=False,
                    height=500,
                    avatar_images=("images/user.png", "images/openai.png")
                )
                chatbot.like(UISettings.feedback, None, None)

            ##############
            # SECOND ROW:
            ##############
            with gr.Row():
                input_txt = gr.Textbox(
                    lines=4,
                    scale=8,
                    placeholder="Enter your question here...",
                    container=False,
                )

            ##############
            # Third ROW:
            ##############
            with gr.Row() as row_two:
                text_submit_btn = gr.Button(value="Submit")
                app_functionality = gr.Dropdown(
                    label="App functionality", 
                    choices=["Chat"], 
                    value="Chat"
                )
                chat_type = gr.Dropdown(
                    label="Chat type", 
                    choices=[
                        "Q&A with stored SQL-DB",
                        "Q&A with stored CSV/XLSX SQL-DB",
                        "Auto-Detect"
                    ], 
                    value="Auto-Detect"
                )
                debug_mode = gr.Checkbox(
                    label="Enable Debug Mode", 
                    value=False
                )
                clear_button = gr.ClearButton([input_txt, chatbot])

            ##############
            # Process:
            ##############
            txt_msg = input_txt.submit(
                fn=ChatBot.respond,
                inputs=[chatbot, input_txt, chat_type, app_functionality, debug_mode],
                outputs=[input_txt, chatbot],
                queue=False
            ).then(lambda: gr.Textbox(interactive=True), None, [input_txt], queue=False)

            txt_msg = text_submit_btn.click(
                fn=ChatBot.respond,
                inputs=[chatbot, input_txt, chat_type, app_functionality, debug_mode],
                outputs=[input_txt, chatbot],
                queue=False
            ).then(lambda: gr.Textbox(interactive=True), None, [input_txt], queue=False)

if __name__ == "__main__":
    demo.launch(share=True)
