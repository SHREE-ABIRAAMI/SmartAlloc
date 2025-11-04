import reflex as rx
from app.states.chatbot_state import ChatbotState, Message


def chat_message(message: Message) -> rx.Component:
    is_user = message["role"] == "user"
    return rx.el.div(
        rx.el.div(
            rx.markdown(
                message["content"],
                class_name="prose prose-invert prose-sm max-w-none",
                component_map={"p": lambda text: rx.el.p(text, class_name="m-0")},
            ),
            class_name=rx.cond(
                is_user,
                "p-3 rounded-lg bg-blue-600 self-end chat-message-user",
                "p-3 rounded-lg bg-gray-700 self-start chat-message-assistant",
            ),
            max_width="80%",
        ),
        class_name="flex flex-col",
        align_items=rx.cond(is_user, "end", "start"),
    )


def chatbot() -> rx.Component:
    return rx.el.div(
        rx.cond(
            ChatbotState.is_chat_open,
            rx.el.div(
                rx.el.div(
                    rx.el.h3("HOD Assistant", class_name="font-bold"),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        on_click=ChatbotState.toggle_chat,
                        class_name="p-1 rounded-full hover:bg-gray-600",
                    ),
                    class_name="flex justify-between items-center p-4 border-b border-gray-600",
                ),
                rx.el.div(
                    rx.foreach(ChatbotState.messages, chat_message),
                    class_name="flex-1 p-4 space-y-4 overflow-y-auto",
                ),
                rx.el.div(
                    rx.el.form(
                        rx.el.input(
                            placeholder="Ask about the timetable...",
                            name="query",
                            class_name="flex-1 px-4 py-2 rounded-lg border border-gray-600 bg-[#0d1117] text-white focus:outline-none",
                            disabled=ChatbotState.processing,
                        ),
                        rx.el.button(
                            rx.icon("send", class_name="h-5 w-5"),
                            type="submit",
                            class_name="p-2 bg-blue-600 rounded-full hover:bg-blue-700",
                            is_loading=ChatbotState.processing,
                        ),
                        on_submit=ChatbotState.handle_submit,
                        reset_on_submit=True,
                        class_name="flex items-center gap-2 p-4 border-t border-gray-600",
                    )
                ),
                class_name="fixed bottom-24 right-6 w-96 h-[32rem] bg-[#1c2128] text-white rounded-2xl shadow-2xl flex flex-col z-50 chatbot-window-animate",
            ),
        ),
        rx.el.button(
            rx.icon("bot", class_name="h-8 w-8"),
            on_click=ChatbotState.toggle_chat,
            class_name="fixed bottom-6 right-6 p-4 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:scale-110 transition-transform",
        ),
    )