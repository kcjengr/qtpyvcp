#include "gcodeeditorplugin.h"
#include "gcodeeditor.h"

GCodeEditorPlugin::GCodeEditorPlugin(QObject *parent)
	: QObject(parent), m_initialized(false)
{
}

QString GCodeEditorPlugin::domXml() const
{
	return "<ui language=\"c++\">\n"
		   " <widget class=\"GCodeEditor\" name=\"gcodeEditor\">\n"
		   "  <property name=\"geometry\">\n"
		   "   <rect>\n"
		   "    <x>0</x>\n"
		   "    <y>0</y>\n"
		   "    <width>400</width>\n"
		   "    <height>300</height>\n"
		   "   </rect>\n"
		   "  </property>\n"
		   " </widget>\n"
		   "</ui>";
}

QWidget *GCodeEditorPlugin::createWidget(QWidget *parent)
{
	return new GCodeEditor(parent);
}

void GCodeEditorPlugin::initialize(QDesignerFormEditorInterface *core)
{
	if (m_initialized)
		return;

	m_initialized = true;
}
