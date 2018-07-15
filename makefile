#Directory with ui and resource files
RESOURCE_DIR = sim

#Directory for compiled resources
COMPILED_DIR = sim

#UI files to compile
UI_FILES = xyz.ui
#Qt resource files to compile
RESOURCES = xyz.qrc

#pyuic5 and pyrcc5 binaries
PYUIC = pyuic5
PYRCC = pyrcc5

#################################
# DO NOT EDIT FOLLOWING

COMPILED_UI = $(UI_FILES:%.ui=$(COMPILED_DIR)/%_ui.py)
COMPILED_RC = $(RESOURCES:%.qrc=$(COMPILED_DIR)/%_rc.py)

all : resources ui

resources : $(COMPILED_RC)

ui : $(COMPILED_UI)

$(COMPILED_DIR)/%_ui.py : $(RESOURCE_DIR)/%.ui
	$(PYUIC) $< -o $@

$(COMPILED_DIR)/%_rc.py : $(RESOURCE_DIR)/%.qrc
	$(PYRCC) $< -o $@

clean :
	$(RM) $(COMPILED_UI) $(COMPILED_RC) $(COMPILED_UI:.py=.pyc) $(COMPILED_RC:.py=.pyc)
