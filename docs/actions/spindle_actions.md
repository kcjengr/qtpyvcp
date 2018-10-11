# Spindle Actions

Spindle action methods available to QtDesigner action widgets.

If the spindle number _**n**_ is omitted, then the action will default
to spindle 0. For example, these will both spin spindle 0 forward at 500rpm:  
`spindle.forward:500`  
`spindle.0.forward:500`


## Spindle Power

Disengage brake and start spindle _**n**_ spinning in the forward direction.
If `speed` is not specified the current interpreter speed setting will be used,
and any overrides applied if override is enabled.  
`spindle.n.forward[:<speed (float)>]`

Identical to above, but starts spindle spinning in the reverse direction.  
`spindle.n.reverse[:<speed (float)>]`

Turn spindle _**n**_ off and engage spindle brake.   
`spindle.n.off`

Increase speed of spindle _**n**_ by 100rpm.  
`spindle.n.faster`

Decrease speed of spindle _**n**_ by 100rpm.  
`spindle.n.slower`


## Spindle Override

Set the override of spindle _**n**_ to a `percent` of commanded speed.
The `percent` argument is required, but if used with an _ActionSpinBox_ or
_ActionSlider_ will be passed automatically.
`spindle.n.override:<percent (int)>`  

Resets the override of spindle _**n**_ to 100% of commanded speed.  
`spindle.n.override.reset`

Enable applying override to spindle _**n**_. Default.  
`spindle.n.override.enable`

Disable applying override to spindle _**n**_.  
`spindle.n.override.disable`

Toggle whether override is applied to spindle _**n**_.  
`spindle.n.override.toggle_enable`


## Spindle Brake

Engage spindle _**n**_ brake.  
`spindle.n.brake.on`

Disengage spindle _**n**_ brake.  
`spindle.n.brake.off`

Toggle engage/disengage of spindle _**n**_ brake. Typically used with checkable
menu action, or an _ActionCheckBox_, but also can be used with an _ActionButton_.   
`spindle.n.brake.toggle`
