#ifndef GCODEEDITORPLUGIN_H
#define GCODEEDITORPLUGIN_H

#include <QObject>


#include <QtUiPlugin/QDesignerCustomWidgetInterface>

class GCodeEditorPlugin : public QObject, public QDesignerCustomWidgetInterface
{
	Q_OBJECT
	Q_PLUGIN_METADATA(IID "org.qt-project.Qt.QDesignerCustomWidgetInterface")
	Q_INTERFACES(QDesignerCustomWidgetInterface)

public:
	GCodeEditorPlugin(QObject *parent = nullptr);

	bool isContainer() const override { return false; }
	bool isInitialized() const override { return m_initialized; }
	QIcon icon() const override { return QIcon(); }
	QString domXml() const override;
	QString group() const override { return "QtPyVCP - Input"; }
	QString includeFile() const override { return "gcodeeditor.h"; }
	QString name() const override { return "GCodeEditor"; }
	QString toolTip() const override { return "G-code Editor Widget"; }
	QString whatsThis() const override { return "A text editor with G-code syntax highlighting"; }
	QWidget *createWidget(QWidget *parent) override;
	void initialize(QDesignerFormEditorInterface *core) override;

private:
	bool m_initialized;
};

#endif // GCODEEDITORPLUGIN_H
