import machine_actions as machine
import program_actions as program
import coolant_actions as coolant

def bindWidget(widget, action):
    try:
        action_class, action = action.split('.', 1)
        globals()[action_class].bindWidget(widget, action)
    except Exception as e:
        print e
        pass
