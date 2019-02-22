==============
Action Buttons
==============

**Syntax**

Action button syntax for the `actionName` is
`group.action.subaction:argument=item`. Some action items take an optional
argument like ``spindle.override.reset:spindle=2`` to reset the override for a
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

-------------------
**Spindle Actions**
-------------------

----------------
**Tool Actions**
----------------
