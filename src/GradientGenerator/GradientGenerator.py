#Author-Kazuya Fujimoto
#Description-Creates microfluidic gradient generater in current sketch

# Flow:
# Check sketch active or not
# Receive input for gradient generator parameters
# Calculate gradient generater shape
# Draw from calculate result
import adsk.core, adsk.fusion, adsk.cam, traceback
# Globals
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_handlers = []

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        cmdDef = _ui.commandDefinitions.itemById('GradPythonScript')
        if not cmdDef:
            # Create a command definition.
            cmdDef = _ui.commandDefinitions.addButtonDefinition('GradPythonScript', 'Grad Generator', 'Creates a gradient generator', './') 
        
        # Connect to the command created event.
        onCommandCreated = GradCommandCreateHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)
        
        # Execute the command.
        cmdDef.execute()

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class GradCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class GradCommandCreateHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            event_args = adsk.core.CommandCreatedEventArgs.cast(args)
            des = adsk.fusion.Design.cast(_app.activeProduct)
            if not des:
                _ui.messageBox('A Fusion design must be active when invoking this command')

            cmd = event_args.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs
            numTeeth = inputs.addStringValueInput('numTeeth', 'Number of Teeth', '0')

             # Connect to the command related events.
            onExecute = GradCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)        
            
            onInputChanged = GradCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)     
            
            onValidateInputs = GradCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

            onDestroy = GradCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the execute event.
class GradCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            event_args = adsk.core.CommandEventArgs.cast(args)
            # Obtain design
            des = adsk.fusion.Design.cast(_app.activeProduct)
            grad_gen = draw_grad_generator(des, 2, 4, 0.005)

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the inputChanged event.
class GradCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            pass
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the validateInputs event.
class GradCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
            
            
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw_grad_generator(design, input_num: int, output_num: int, resistor_rad: float):
    try:
        # Create a new component by creating an occurrence.
        occs = design.rootComponent.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)        
        newComp = adsk.fusion.Component.cast(newOcc.component)
        
        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        baseSketch = sketches.add(xyPlane)
        baseSketch.isComputeDeferred = True
        # Draw a circle for the base.
        original_point = adsk.core.Point3D.create(0, 0, 0)
        for i in range(input_num+1, output_num+1):
            original_point = draw_grad_stage(sketches, xyPlane, newComp, original_point, i, 0.5, 0.5, 0.02, 2, 0.02, 0.3)

        baseSketch.isComputeDeferred = False
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw_grad_stage(sketches, plane, comp,
                     original_point, unit_num: int,
                     connect_width: float, height: float,
                     channel_width: float, curve_num: int,
                     curve_rad: float, resistor_width: float):

    # Draw connecting channel
    sketch = sketches.add(plane)
    connecting = sketch.sketchCurves.sketchLines
    left_end = adsk.core.Point3D.create(original_point.x - (unit_num - 1) * connect_width/2, original_point.y, original_point.z)
    right_end = adsk.core.Point3D.create(original_point.x - (unit_num - 2) * connect_width/2, original_point.y + channel_width, original_point.z)
    connecting.addTwoPointRectangle(left_end, right_end)

    sketch = draw_single_grad(sketches, plane, comp, left_end,
                     connect_width, height,
                     channel_width, curve_num,
                     curve_rad, resistor_width)
    

    extrudes = comp.features.extrudeFeatures
    
    prof = sketch.profiles.item(0)
    ext_input = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(0.2)
    ext_input.setDistanceExtent(False, distance)
    channel_extrude = extrudes.add(ext_input)

    prof = sketch.profiles.item(1)
    ext_input = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(0.2)
    ext_input.setDistanceExtent(False, distance)
    channel_extrude = extrudes.add(ext_input)

    prof = sketch.profiles.item(2)
    ext_input = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(0.2)
    ext_input.setDistanceExtent(False, distance)
    channel_extrude = extrudes.add(ext_input)

    # Create input entities for ractangular pattern
    input_entities = adsk.core.ObjectCollection.create()

    
    # Get the body created by extrusion
    for i in range(extrudes.count):

        body = extrudes.item(i)

        input_entities.add(body)

    x_axis = comp.xConstructionAxis
    y_axis = comp.yConstructionAxis

    # Quantity and distance

    quantity_one = adsk.core.ValueInput.createByString('{}'.format(unit_num))
    
    distance_one = adsk.core.ValueInput.createByReal(connect_width)
    quantity_two = adsk.core.ValueInput.createByString('{}'.format(1))
    distance_two = adsk.core.ValueInput.createByReal(0)

    # Create the input for rectangular pattern
    rectangular_pattern = comp.features.rectangularPatternFeatures
    rectangular_pattern_input = rectangular_pattern.createInput(input_entities, x_axis, quantity_one, distance_one,
                                                                adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    
    # Set the data for second direction
    rectangular_pattern_input.setDirectionTwo(y_axis, quantity_two, distance_two)

    #Create the rectangular pattern
    rectangula_feature = rectangular_pattern.add(rectangular_pattern_input)

    for i in range(1, unit_num-1):
        left_end = adsk.core.Point3D.create(original_point.x - (unit_num  - 2 * i) * connect_width/2, original_point.y, original_point.z)
        right_end = adsk.core.Point3D.create(original_point.x - (unit_num - 2 * (i + 1)) * connect_width/2, original_point.y + channel_width, original_point.z)
        connecting.addTwoPointRectangle(left_end, right_end)
        single_original = adsk.core.Point3D.create(left_end.x + connect_width/2, left_end.y, left_end.z)
        draw_single_grad(sketches, plane,
                        comp, single_original,
                        connect_width, height,
                        channel_width, curve_num,
                        curve_rad, resistor_width)
    
    left_end = adsk.core.Point3D.create(original_point.x + (unit_num -2) * connect_width/2, original_point.y + channel_width, original_point.z)
    right_end = adsk.core.Point3D.create(original_point.x + (unit_num - 1) * connect_width/2, original_point.y, original_point.z)
    connecting.addTwoPointRectangle(left_end, right_end)

    draw_single_grad(sketches, plane, comp, right_end, 
                     connect_width, height,
                     channel_width, curve_num,
                     curve_rad, resistor_width)

    return adsk.core.Point3D.create(original_point.x, original_point.y + height, original_point.z)


def draw_single_grad(sketches, plane,
                     comp, original_point,
                     connect_width: float, height: float,
                     channel_width: float, curve_num: int,
                     curve_rad: float, resistor_width: float):
    

    # Draw connecting channel
    sketch = sketches.add(plane)
    #connecting = sketch.sketchCurves.sketchLines
    
    # Draw resistor part
    # - Straight part
    channel = sketch.sketchCurves
    straight_len = (height - (curve_rad * 4 * curve_num))/2
    top_left = adsk.core.Point3D.create(original_point.x - channel_width/2, original_point.y, original_point.z)
    bottom_right = adsk.core.Point3D.create(original_point.x + channel_width/2, original_point.y + straight_len, original_point.z)
    channel.sketchLines.addTwoPointRectangle(top_left, bottom_right)

    resistor_org = adsk.core.Point3D.create(original_point.x,
                                            original_point.y + straight_len,
                                            original_point.z)

    start_top = adsk.core.Point3D.create(original_point.x - channel_width/2, original_point.y+straight_len, original_point.z)
    start_bottom = adsk.core.Point3D.create(original_point.x - channel_width/2, original_point.y+straight_len+channel_width, original_point.z)
    channel.sketchLines.addByTwoPoints(start_top, start_bottom)

    for i in range(0, curve_num):
        resistor_org = gen_resistor_part(channel, resistor_org, channel_width, curve_num,
                      curve_rad, resistor_width)
    end_top = adsk.core.Point3D.create(resistor_org.x-channel_width/2, resistor_org.y, original_point.z)
    end_bottom = adsk.core.Point3D.create(resistor_org.x-channel_width/2, resistor_org.y+channel_width, original_point.z)
    channel.sketchLines.addByTwoPoints(end_top, end_bottom)
    
    top_left = adsk.core.Point3D.create(resistor_org.x - channel_width/2,
                                        resistor_org.y,
                                        original_point.z)
    bottom_right = adsk.core.Point3D.create(resistor_org.x + channel_width/2,
                                            resistor_org.y + straight_len,
                                            original_point.z)
    channel.sketchLines.addTwoPointRectangle(top_left, bottom_right)

    return sketch

def gen_resistor_part(channel, original_point,
                      channel_width: float, curve_num: int,
                      curve_rad: float, resistor_width: float) -> adsk.core.Point3D:
    

    # - Curve part
    top_left = adsk.core.Point3D.create(original_point.x - channel_width/2, 
                                        original_point.y, 
                                        original_point.z)

    top_right = adsk.core.Point3D.create(original_point.x + resistor_width/2, 
                                        original_point.y, 
                                        original_point.z)
    
    bottom_left = adsk.core.Point3D.create(original_point.x - channel_width/2,
                                            original_point.y + channel_width, 
                                            original_point.z)

    bottom_right = adsk.core.Point3D.create(original_point.x + resistor_width/2,
                                            original_point.y + channel_width, 
                                            original_point.z)

    channel.sketchLines.addByTwoPoints(top_left, top_right)
    channel.sketchLines.addByTwoPoints(bottom_left, bottom_right)
    

    #channel.sketchLines.addTwoPointRectangle(top_left, bottom_right)

    # -- Outer arc
    curve_start = adsk.core.Point3D.create(bottom_right.x, top_left.y, top_left.z)
    midPoint = adsk.core.Point3D.create(bottom_right.x + curve_rad + channel_width /2,
                                        top_left.y + channel_width/2 + curve_rad, 
                                        bottom_right.z)
    curve_end = adsk.core.Point3D.create(bottom_right.x, 
                                         top_left.y + curve_rad * 2 + channel_width, 
                                         top_left.z)
    channel.sketchArcs.addByThreePoints(curve_start, midPoint, curve_end)

    # -- Inner arc
    curve_start = adsk.core.Point3D.create(bottom_right.x,
                                           top_left.y + channel_width,
                                           top_left.z)
    midPoint = adsk.core.Point3D.create(bottom_right.x + curve_rad - channel_width /2,
                                        top_left.y + channel_width/2 + curve_rad,
                                        bottom_right.z)
    curve_end = adsk.core.Point3D.create(bottom_right.x, 
                                         top_left.y + curve_rad  * 2,
                                         top_left.z)
    channel.sketchArcs.addByThreePoints(curve_start, midPoint, curve_end)

    bottom_left = adsk.core.Point3D.create(curve_end.x-resistor_width, 
                                        curve_end.y, 
                                        original_point.z)
    
    top_left = adsk.core.Point3D.create(curve_end.x - resistor_width, 
                                        curve_end.y + channel_width, 
                                        original_point.z)

    top_right = adsk.core.Point3D.create(curve_end.x, 
                                        curve_end.y + channel_width, 
                                        original_point.z)
    
    channel.sketchLines.addByTwoPoints(top_left, top_right)
    channel.sketchLines.addByTwoPoints(curve_end, bottom_left)
    #channel.sketchLines.addTwoPointRectangle(top_left, curve_end)

    # -- Outer arc
    curve_start = adsk.core.Point3D.create(top_left.x,
                                           top_left.y - channel_width,
                                           top_left.z)
    midPoint = adsk.core.Point3D.create(top_left.x - curve_rad - channel_width/2,
                                        top_left.y + curve_rad - channel_width/2, 
                                        top_left.z)
    curve_end = adsk.core.Point3D.create(top_left.x, top_left.y + curve_rad*2)
    channel.sketchArcs.addByThreePoints(curve_start, midPoint, curve_end)

    # -- Inner arc
    curve_start = adsk.core.Point3D.create(top_left.x,
                                           top_left.y,
                                           top_left.z)
    midPoint = adsk.core.Point3D.create(top_left.x - curve_rad + channel_width/2,
                                        top_left.y + curve_rad - channel_width/2, 
                                        top_left.z)
    curve_end = adsk.core.Point3D.create(top_left.x, top_left.y + curve_rad*2 - channel_width)
    channel.sketchArcs.addByThreePoints(curve_start, midPoint, curve_end)

    bottom_right = adsk.core.Point3D.create(curve_end.x + resistor_width/2-channel_width/2,
                                            curve_end.y, 
                                            original_point.z)
    
    bottom_left = adsk.core.Point3D.create(curve_end.x,
                                        curve_end.y, 
                                        original_point.z)


    top_right = adsk.core.Point3D.create(curve_end.x + resistor_width/2-channel_width/2, 
                                        curve_end.y + channel_width, 
                                        original_point.z) 

    
    
    top_left = adsk.core.Point3D.create(curve_end.x, 
                                        curve_end.y + channel_width, 
                                        original_point.z)

    channel.sketchLines.addByTwoPoints(top_left, top_right)
    channel.sketchLines.addByTwoPoints(bottom_right, bottom_left)    
    #channel.sketchLines.addTwoPointRectangle(top_left, bottom_right)
    new_org = bottom_right = adsk.core.Point3D.create(curve_end.x + resistor_width/2,
                                            curve_end.y, 
                                            original_point.z)
    return new_org
