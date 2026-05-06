"""GCode Editor Configuration Utility

Applies YAML configuration to GCodeEditor widgets.
Single source of truth for editor styling and syntax highlighting.
"""

from PySide6.QtGui import QColor, QFont
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

# Qt6 font weight mapping: integer values → QFont.Weight enum
def _map_font_weight(weight_value):
    """Convert integer or string weight to QFont.Weight enum."""
    if isinstance(weight_value, str):
        weight_value = int(weight_value)
    
    # Map common weight values to Qt6 enums
    # Qt6 uses QFont.Weight enum instead of raw integers
    if weight_value <= 100:
        return QFont.Weight.Thin
    elif weight_value <= 200:
        return QFont.Weight.ExtraLight
    elif weight_value <= 300:
        return QFont.Weight.Light
    elif weight_value <= 400:
        return QFont.Weight.Normal
    elif weight_value <= 500:
        return QFont.Weight.Medium
    elif weight_value <= 600:
        return QFont.Weight.DemiBold
    elif weight_value <= 700:
        return QFont.Weight.Bold
    elif weight_value <= 800:
        return QFont.Weight.ExtraBold
    else:
        return QFont.Weight.Black


def apply_yaml_config_to_editor(editor, config_dict):
    """Apply YAML configuration to a GCodeEditor widget.
    
    Args:
        editor: GCodeEditor widget instance
        config_dict: Full config dictionary containing gcode_editor_style_defaults 
                     and gcode_syntax_profile keys
    """
    if editor is None:
        LOG.warning("Cannot apply config to None editor")
        return
    
    editor_name = editor.objectName() if hasattr(editor, 'objectName') else 'unnamed'
    LOG.debug(f"Applying YAML config to editor: {editor_name}")
    
    # Apply visual/display properties
    style_config = config_dict.get('gcode_editor_style_defaults', {})
    if style_config:
        _apply_display_properties(editor, style_config)
    else:
        LOG.warning("No gcode_editor_style_defaults found in config")
    
    # Apply syntax highlighting
    syntax_config = config_dict.get('gcode_syntax_profile', {})
    if syntax_config:
        _apply_syntax_highlighting(editor, syntax_config, style_config)
    else:
        LOG.warning("No gcode_syntax_profile found in config")


def _apply_display_properties(editor, style_config):
    """Apply visual display properties to editor widget."""
    
    if not style_config:
        LOG.warning("No style_config provided to _apply_display_properties")
        return
    
    # Build stylesheet for main editor widget (background, text, font, padding, border)
    stylesheet_parts = []
    if 'background_color' in style_config:
        stylesheet_parts.append(f"background-color: {style_config['background_color']};")
    if 'text_color' in style_config:
        stylesheet_parts.append(f"color: {style_config['text_color']};")
    if 'padding' in style_config:
        stylesheet_parts.append(f"padding: {style_config['padding']}px;")
    if 'border_radius' in style_config:
        stylesheet_parts.append(f"border-radius: {style_config['border_radius']}px;")
    
    # Font styling via stylesheet
    if 'font_family' in style_config:
        stylesheet_parts.append(f"font-family: '{style_config['font_family']}';")
    if 'font_point_size' in style_config:
        stylesheet_parts.append(f"font-size: {style_config['font_point_size']}pt;")
    if 'font_weight' in style_config:
        weight = style_config['font_weight']
        # Map numeric weights to CSS
        if isinstance(weight, int):
            stylesheet_parts.append(f"font-weight: {weight};")
        else:
            stylesheet_parts.append(f"font-weight: {weight};")
    if 'font_style' in style_config:
        stylesheet_parts.append(f"font-style: {style_config['font_style']};")
    if 'letter_spacing' in style_config:
        stylesheet_parts.append(f"letter-spacing: {style_config['letter_spacing']}px;")
    if 'word_spacing' in style_config:
        stylesheet_parts.append(f"word-spacing: {style_config['word_spacing']}px;")
    
    if stylesheet_parts:
        stylesheet = "GCodeEditor { " + " ".join(stylesheet_parts) + " }"
        editor.setStyleSheet(stylesheet)
        LOG.debug(f"Applied stylesheet: {stylesheet}")
    
    # Line number area styling - match Q_PROPERTY names exactly
    if 'line_number_area_background' in style_config:
        color = QColor(style_config['line_number_area_background'])
        editor.setProperty('lineNumberAreaBackground', color)
    
    if 'line_number_area_color' in style_config:
        color = QColor(style_config['line_number_area_color'])
        editor.setProperty('lineNumberAreaColor', color)
    
    # Line number font - these properties are separate, not bundled in a QFont
    if 'line_number_font_family' in style_config:
        editor.setProperty('lineNumberFontFamily', style_config['line_number_font_family'])
    
    if 'line_number_font_point_size' in style_config:
        editor.setProperty('lineNumberFontPointSize', int(style_config['line_number_font_point_size']))
    
    if 'line_number_font_weight' in style_config:
        weight = _map_font_weight(style_config['line_number_font_weight'])
        editor.setProperty('lineNumberFontWeight', weight)
    
    if 'line_number_font_italic' in style_config:
        editor.setProperty('lineNumberFontItalic', bool(style_config['line_number_font_italic']))
    
    # Current line highlighting
    if 'current_line_highlight_enabled' in style_config:
        enabled = bool(style_config['current_line_highlight_enabled'])
        editor.setProperty('currentLineHighlightEnabled', enabled)
    
    if 'current_line_background' in style_config:
        color = QColor(style_config['current_line_background'])
        editor.setProperty('currentLineBackground', color)
    
    if 'current_line_color' in style_config:
        color = QColor(style_config['current_line_color'])
        editor.setProperty('currentLineColor', color)
    
    # Find/replace highlight colors
    if 'find_highlight_background' in style_config:
        color = QColor(style_config['find_highlight_background'])
        editor.setProperty('findHighlightBackground', color)
    
    if 'find_highlight_text' in style_config:
        color = QColor(style_config['find_highlight_text'])
        editor.setProperty('findHighlightText', color)
    
    if 'find_error_background' in style_config:
        color = QColor(style_config['find_error_background'])
        editor.setProperty('findErrorBackground', color)
    
    if 'find_error_text' in style_config:
        color = QColor(style_config['find_error_text'])
        editor.setProperty('findErrorText', color)
    
    if 'find_status_background' in style_config:
        color = QColor(style_config['find_status_background'])
        editor.setProperty('findStatusBackground', color)
    
    if 'find_status_text' in style_config:
        color = QColor(style_config['find_status_text'])
        editor.setProperty('findStatusText', color)
    
    if 'find_status_border' in style_config:
        color = QColor(style_config['find_status_border'])
        editor.setProperty('findStatusBorder', color)


def _apply_syntax_highlighting(editor, syntax_config, style_config):
    """Apply dynamic syntax highlighting configuration to editor.
    
    Builds token→color mapping from YAML syntax_styles and passes to C++.
    - User can define unlimited syntax_style groups with any tokens
    - Each token gets the color from its syntax_style group
    - If a token appears in multiple groups, last one wins
    - C++ handles pattern matching and formatting rules
    """
    
    # Build token→color mapping from all syntax_styles
    token_color_map = {}
    syntax_styles = syntax_config.get('syntax_styles', [])
    
    LOG.info(f"Building dynamic token color map from {len(syntax_styles)} syntax_style groups")
    
    for style in syntax_styles:
        style_id = style.get('id', 'unknown')
        color = style.get('color')
        
        if not color:
            LOG.warning(f"Syntax style '{style_id}' missing color, skipping")
            continue
        
        # Validate color
        qcolor = QColor(color)
        if not qcolor.isValid():
            LOG.warning(f"Syntax style '{style_id}' has invalid color '{color}', skipping")
            continue
        
        # Map all tokens in this style to this color
        tokens = style.get('tokens', [])
        for token in tokens:
            token_color_map[token] = qcolor
            LOG.debug(f"  Token '{token}' → {color} (from {style_id})")
    
    # Pass to C++ editor (PySide6 auto-converts Python dict to QVariantMap)
    # Verify methods exist (plugin promotion timing issue)
    if not hasattr(editor, 'setTokenColorMap'):
        LOG.warning("Editor missing setTokenColorMap method - plugin not fully promoted yet, skipping syntax highlighting")
        return
    
    if len(token_color_map) > 0:
        editor.setTokenColorMap(token_color_map)
        editor.setProperty('syntaxHighlightingEnabled', True)
        LOG.info(f"Syntax highlighting enabled with {len(token_color_map)} token types")
    else:
        editor.clearTokenColorMap()
        editor.setProperty('syntaxHighlightingEnabled', False)
        LOG.info("Syntax highlighting disabled (no tokens defined)")
