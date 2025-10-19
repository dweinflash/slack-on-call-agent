from slack_bolt import App
from .ask_command import ask_callback
from .code_command import code_callback
from .incident_command import incident_callback


def register(app: App):
    app.command("/ask-bolty")(ask_callback)
    app.command("/code")(code_callback)
    app.command("/incident")(incident_callback)
