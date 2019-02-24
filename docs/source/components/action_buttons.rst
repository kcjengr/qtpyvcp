==============
Action Buttons
==============

**Syntax**

Action button syntax for the `actionName` is
`group.action.subaction:argument=item`. Some action items take an optional
argument like ``spindle.override.reset:2`` to reset the override for a
spindle number 2.

-------------------
**Coolant Actions**
-------------------

**Flood** `actionNames` for `ActionButtons`
::

    coolant.flood.off
    coolant.flood.on
    coolant.flood.toggle

**Mist** `actionNames` for `ActionButtons`
::

    coolant.mist.off
    coolant.mist.on
    coolant.mist.toggle

-------------------
**Machine Actions**
-------------------

**E Stop** `actionNames` for `ActionButtons`
::

    machine.estop.activate
    machine.estop.reset
    machine.estop.toggle

**Feed Override** `actionNames` for `ActionButtons`
::

    machine.feed-override.disable
    machine.feed-override.enable
    machine.feed-override.reset
    machine.feed-override.set:value
    machine.feed-override.toggle-enable

**Home** `actionNames` for `ActionButtons`
::

    machine.home.all
    machine.home.axis:axis letter
    machine.home.joint:joint number

**Issue MDI** `actionNames` for `ActionButtons`
Note: Use the MDIButton for MDI commands
::

    machine.issue-mdi:command

**Jog** `actionNames` for `ActionButtons`
::

    machine.jog.axis.axis letter,direction,speed,distance
    machine.jog.set-angular-speed.value
    machine.jog.set-increment.raw increment
    machine.jog.set-jog-continuous
    machine.jog.set-linear-speed.value

**Jog Mode** `actionNames` for `ActionButtons`
::

    machine.jog-mode.continuous
    machine.jog-mode.incremental
    machine.jog-mode.toggle

**Max Velocity** `actionNames` for `ActionButtons`
::

    machine.max-velocity.set
    machine.max-velocity.reset

**Mode** `actionNames` for `ActionButtons`
::

    machine.mode.auto
    machine.mode.manual
    machine.mode.toggle

**Power** `actionNames` for `ActionButtons`
::

    machine.power.off
    machine.power.on
    machine.power.toggle

**UnHome** `actionNames` for `ActionButtons`
::

    machine.unhome.all
    machine.unhome.axis:axis letter
    machine.unhome.joint:joint number

-------------------
**Program Actions**
-------------------

**Abort** `actionNames` for `ActionButtons`
::

    program.abort

**Block Delete** `actionNames` for `ActionButtons`
::

    program.block-delete.off
    program.block-delete.on
    program.block-delete.toggle

**Optional Skip** `actionNames` for `ActionButtons`
::

    program.

**Optional Stop** `actionNames` for `ActionButtons`
::

    program.option-stop.off
    program.optional-stop.on
    program.optional-stop.toggle

**Pause Program** `actionNames` for `ActionButtons`
::

    program.pause

**Resume Program** `actionNames` for `ActionButtons`
::

    program.resume

**Run Program** `actionNames` for `ActionButtons`

Run has an optional argument `start line`, replace `n` with the line number.
::

    program.run
    program.run:n

**Step Program** `actionNames` for `ActionButtons`
::

    program.step

-------------------
**Spindle Actions**
-------------------

Spindle Actions have an optional argument `spindle`, if left off spindle 0 is
assumed. To specifiy a spindle replace `spindle` in the examples with the
spindle number.


**Brake** `actionNames` for `ActionButtons`
::

    spindle.brake.off
    spindle.brake.off:spindle
    spindle.brake.on
    spindle.brake.on:spindle
    spindle.brake.toggle
    spindle.brake.toggle:spindle

**Faster** `actionNames` for `ActionButtons`

Increase spindle speed by 100rpm
::

    spindle.faster
    spindle.faster:spindle

**Forward** `actionNames` for `ActionButtons`

Turn spindle on in the forward direction
::

    spindle.forward
    spindle.forward:speed
    spindle.forward:speed,spindle

**Off** `actionNames` for `ActionButtons`
::

    spindle.off
    spindle.off:spindle

**Override** `actionNames` for `ActionButtons`

Set spindle override percentage. Used with an ActionSlider you can omit the
speed.
::

    spindle.override
    spindle.override:speed
    spindle.override:speed,spindle

**Reverse** `actionNames` for `ActionButtons`
::

    spindle.reverse
    spindle.reverse:speed
    spindle.reverse:speed,spindle

**Slower** `actionNames` for `ActionButtons`

Decrease spindle speed by 100rpm
::

    spindle.slower
    spindle.slower:spindle

----------------
**Tool Actions**
----------------

**Calibration** `actionNames` for `ActionButtons`
::

    tool_actions.calibration

**Halmeter** `actionNames` for `ActionButtons`
::

    tool_actions.halmeter

**Halscope** `actionNames` for `ActionButtons`
::

    tool_actions.halscope

**Halshow** `actionNames` for `ActionButtons`
::

    tool_actions.halshow

**Simulate Probe** `actionNames` for `ActionButtons`
::

    tool_actions.simulate_probe

**Status** `actionNames` for `ActionButtons`
::

    tool_actions.status

