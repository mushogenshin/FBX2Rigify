# TRCR is a Maya rigging tool, it uses Advanced Skeleton for all the rigging jobs. I just invented a different way to use it.
# The goal is to fasten the process of (Adv Skel) rigging, the user just needs to select faces or objects then submit.
# And leave all the hard stuffs for machine (placing joints, skinning, adjust control curves, attach props to character, making proxy version)
# TRCR stands for Truong Concept Rig >> the goal is for anyone using Maya, can Rig, even concept artist. Hopefully. That’s why it has this name.
# Created by Truong Cg Artist gumroad.com/TruongCgArtist
# With help from Mr Trong Hoan mushogenshin.com
# Support: cvbtruong@gmail.com or truongcgartist@gmail.com

import sys
import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import re
from collections import namedtuple
from math import fmod
from math import pow, sqrt
from os import listdir
from os.path import isfile, join

IS_PY2 = sys.version_info.major < 3
MAYA_VERSION = int(cmds.about(v=True))
NGSKINTOOLS_VERSION = None

MllInterface = None

def load_generic_ngskintools():
    """
    Attempt to load ngSkinTools (version 1) first, then, if failed, version 2.
    """
    if MAYA_VERSION >= 2022:
        # ngSkinTools (version 1) is no longer supported in Maya 2022,
        load_ngskintools2()
    else:
        # user might be using either ngSkinTools 1 or 2
        try:
            # firstly, see if ngSkinTools is installed, as
            cmds.loadPlugin('ngSkinTools')  
        except RuntimeError:
            cmds.warning("Failed to load ngSkinTools (version 1) plugin, attempting to load version 2")
            load_ngskintools2()
        else:
            NGSKINTOOLS_VERSION = 1
            # this provides all the ngSkinTools cmds we need for relaxing skinweights
            from ngSkinTools.mllInterface import MllInterface
            from ngSkinTools.layerUtils import LayerUtils

def load_ngskintools2():
    """
    Try loading ngSkinTools2  plugin.
    """
    try:
        cmds.loadPlugin('ngSkinTools2') 
    except RuntimeError:
        cmds.error("ngSkinTools cannot be found, relaxing skinweights won't be executed")
    else:
        NGSKINTOOLS_VERSION = 2
        # TODO: we must use API of ngSkinTools2 and above
        cmds.warning("Access to ngSkinTools (version 2) is not yet supported. Please do your smooth skinning manually.")


# Modify ngSkinTools's `MllInterface` if imports succeed.
load_generic_ngskintools()

# -------------------------------------------------------------------------------

# Advanced Skeleton path.
AdvancedSkeletonPath = None
AdvancedSkeletonPathTF = "adv_skel_path_text_field"

jointSizeFloatSlider = "joint_size_slider"

# Body meshes >> if multiple, then merge them first
originalBodyMeshes = []
originalBodyMeshesTF = "original_body_meshes_tf"

# Deformed Props >> copy skin over later. Add it to TRCR_Grp & hide
deformedProps = []
deformedPropsTF = "deformed_props_tf"
# Non deformed Props >> use auto attach script. Add it to TRCR_Grp & hide
nonDeformedProps = []
nonDeformedPropsTF = "non_deformeed_props_tf"

# Face Items >> just hide, then show them later in FaceItems tab
faceItems = []
faceItemsTF = "face_items_tf"

# End joints list.
endJointsList = []

# Will add more joint with X axis is locked as middle joints.
# Should only be one Root joint, Global is for consistency. These first joints are for defining tabs
firstMiddleFitJointsGlobal = []

# middle fit joints (first list of middleFitJointsGlobal since Advanced Skeleton doesn't accept multiple mid joints
middleFitJoints = []
# torso fit joints will exclude iKSplineJoints
torsoFitJoints =[]

# Chesk IK-labeled joints. Should only one chest joint
chestFitJointsGlobal = []

# Leg could be multiple branches
firstLegFitJointsGlobal = []
legFitJointsGlobal = [[]]

# foot or Ankle joints
footFitJointsGlobal = []

# hand fit joints
handFitJointsGlobal = []

# Toes could be multiple branches when there is multiple Toes* IK label
toesFitJointGlobal = []
toesIndividualFitJointsGlobal = [[]]

# qToes for cat
qToesFitJointGlobal = []

# Arm could be multiple branches
firstArmFitJointsGlobal = []
armFitJointsGlobal = [[]]

# IK Spline joints
firstIKSplineFitJointsGlobal = []
iKSplineFitJointsGlobal = [[]]

# Face items. Define "Head" by Eye IK label. Could be multiple Heads.
eyeFitJointsGlobal = []
headFitJointsGlobal = []
faceItemsFitJointsGlobal = [[]]

# Big Toe IK-labeled joints
bigToeFitJointsGlobal = []

# Pinky Toe IK-labeled joints
pinkyToeFitJointsGlobal = []

# Heel Toe IK-labeled joints
heelFitJointsGlobal = []

# ToesEnd IK-labeled joints
toesEndFitJointsGlobal = []

# Mid Spine IK-labeled joints. Should be just one joint.
midFitJointGlobal = []

# Fingers could be multiple branches when there is multiple Hand* IK label
fingersFitJointsGlobal = [[]]

# FK
fKFitJointsGlobal = [[]]

# deform Joint Meshes
deformJointMeshesList = []

# pair = [[deformJointName, deformJointMesh]]
pairJointsMeshesGlobal = []

trsUI_ID = "Truong_Concept_Rig"

masterTabs = None

toolWindowWidth = 500

toBeDeletedLayoutAll = []

fitFileOptionMenu = None

fitSkeletonsDir = None

fitExtraLimbOptionMenu = None

limbDir = None

torsoCutButtons = []
torsoAddButtons = []
torsoClearButtons = []

armCutButtonsGlobal = []
armAddButtonsGlobal = []
armClearButtonsGlobal = []

fingersCutButtonsGlobal = []
fingersAddButtonsGlobal = []
fingersClearButtonsGlobal = []

legCutButtonsGlobal = []
legAddButtonsGlobal = []
legClearButtonsGlobal = []

toesCutButtonsGlobal = []
toesAddButtonsGlobal = []
toesClearButtonsGlobal = []

faceCutButtonsGlobal = []
faceAddButtonsGlobal = []
faceClearButtonsGlobal = []

ikSplinesCutButtonsGlobal = []
ikSplinesAddButtonsGlobal = []
ikSplinesClearButtonsGlobal = []

fkCutButtonsGlobal = []
fkAddButtonsGlobal = []
fkClearButtonsGlobal = []

smoothTime = 3
smoothTimeField = "smooth_time_field"

bindingJointsList = []

mainRigControl = "Main"
pairBodyMesh_PropListGlobal = []

mainBodyMesh = None
mainBodyMeshTF = "main_body_mesh_text_field"

proxyMeshes = []

allFitJoints = []

meshesSize = []

eyeCenterLoc = None
eyeCenterLocTF = "eye_center_loop_text_field"

# Variables for Attach Props tool
propList = []
propList_tf = "prop_list_text_field"
mainBody = None
mainBody_tf = "main_body_text_field"
controlCheck = False
mainRigControl = None
mainRigControl_tf = "main_rig_control_text_field"
win_ID = "Attach_Props_To_Character_Surface_Tool"
customPivotVertexList = []
customPivotVertexList_tf = "custom_pivot_text_field"

labels = ["Root","Chest","Mid","Hip","Foot","Heel","Toes","ToesEnd","BigToe","PinkyToe","LegAim","QToes","Shoulder","Hand","0","1","2","3"]
attributes = ["twist/bendy","inbetween","global","aim","wheel","freeOrient","worldOrient","flipOrient","noMirror","noFlip","noControl","noSkin",
	"ikLocal","centerBtwFeet","hipSwinger","geoAttach","aimAt","curveGuide","rootOptions"]

iKLabelOptionMenu = None
attrOptionMenu = None
#################################
# Work with fit joint variables #
#################################

# auto fix joints with same name
# auto fix same IKLabel
def autoRenamingDuplicateObjects():
    # find and auto fix the all items that have same name

    # this function is from Erwan Leroy erwanleroy.com/maya-python-renaming-duplicate-objects
    # Find all objects that have the same shortname as another
    # We can indentify them because they have | in the name
    duplicates = [f for f in cmds.ls() if '|' in f]
    # Sort them by hierarchy so that we don't rename a parent before a child.
    duplicates.sort(key=lambda obj: obj.count('|'), reverse=True)

    # if we have duplicates, rename them

    if duplicates:
        for name in duplicates:
            # extract the base name
            m = re.compile("[^|]*$").search(name)
            shortname = m.group(0)

            # extract the numeric suffix
            m2 = re.compile(".*[^0-9]").match(shortname)
            if m2:
                stripSuffix = m2.group(0)
            else:
                stripSuffix = shortname

            # rename, adding '#' as the suffix, which tells maya to find the next available number
            newname = cmds.rename(name, (stripSuffix + "#"))
            print("renamed %s to %s" % (name, newname))

        return "Renamed %s objects with duplicated name." % len(duplicates)
    else:
        return "No Duplicates"

# find all important IKLabel joints. Return a list of them
def findIKLabelJoint(joint):
    global firstMiddleFitJointsGlobal
    global firstArmFitJointsGlobal
    global firstLegFitJointsGlobal
    global firstIKSplineFitJointsGlobal
    global toesFitJointGlobal
    global bigToeFitJointsGlobal
    global pinkyToeFitJointsGlobal
    global footFitJointsGlobal
    global eyeFitJointsGlobal
    global midFitJointGlobal
    global chestFitJointsGlobal
    global heelFitJointsGlobal
    global toesEndFitJointsGlobal
    global handFitJointsGlobal

    # these important joints need to turn draw label on then turn them back later
    # need to turn on drawLabel for Eye, Shoulder, Wrist, Hip and Foot

    previousDrawLabelStatus = cmds.getAttr(joint + ".drawLabel")

    attrPreCheck = cmds.getAttr(joint+".type")

    # shoulder
    if attrPreCheck == 10:
        cmds.setAttr(joint + ".drawLabel", 1)

    # wrist
    if attrPreCheck == 12:
        cmds.setAttr(joint + ".drawLabel", 1)

    # hip
    if attrPreCheck == 2:
        cmds.setAttr(joint + ".drawLabel", 1)

    # foot
    if attrPreCheck == 4:
        cmds.setAttr(joint + ".drawLabel", 1)


    attrOtherPreCheck = cmds.getAttr(joint + ".otherType")

    if attrOtherPreCheck.startswith("Eye"):
        cmds.setAttr(joint + ".drawLabel", 1)

    if attrOtherPreCheck.startswith("Shoulder"):
        cmds.setAttr(joint + ".drawLabel", 1)

    if attrOtherPreCheck.startswith("Wrist"):
        cmds.setAttr(joint + ".drawLabel", 1)

    if attrOtherPreCheck.startswith("Hip"):
        cmds.setAttr(joint + ".drawLabel", 1)

    if attrOtherPreCheck.startswith("Foot"):
        cmds.setAttr(joint + ".drawLabel", 1)

    if attrOtherPreCheck.startswith("Chest"):
        cmds.setAttr(joint + ".drawLabel", 1)

    drawLabelStatus = cmds.getAttr(joint+".drawLabel")

    if drawLabelStatus:
        attr = cmds.getAttr(joint+".type")
        print(attr)
        # 1 = Root
        # 2 = Hip
        # 5 = Toe
        # 24 = Big Toe
        # 28 = Pinky Toe
        # 10 = Shoulder
        # 12 = Hand
        # Any other joint could be named using .otherType and rename
        # 18 = Other + ".otherType" = "Mid" >> Mid joint
        # 18 = Other + ".otherType" = "Eye"
        # 18 = Other + ".otherType" = "0" >> IKSpline
        # 18 = Other + ".otherType" = "Chest"
        if attr == 1:
            # This is root joint. Should only have one.
            firstMiddleFitJointsGlobal.append(joint)
            print(firstMiddleFitJointsGlobal)
        elif attr == 2:
            # Hip joints
            firstLegFitJointsGlobal.append(joint)
            print(firstLegFitJointsGlobal)
            cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
        elif attr == 12:
            # hand joints
            handFitJointsGlobal.append(joint)
            cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
        elif attr == 5:
            toesFitJointGlobal.append(joint)
            print(toesFitJointGlobal)
        elif attr == 24:
            bigToeFitJointsGlobal.append(joint)
            print(bigToeFitJointsGlobal)
        elif attr == 28:
            pinkyToeFitJointsGlobal.append(joint)
            print(pinkyToeFitJointsGlobal)
        elif attr == 10:
            # shoulder
            firstArmFitJointsGlobal.append(joint)
            print(firstArmFitJointsGlobal)
            cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
        elif attr == 4:
            footFitJointsGlobal.append(joint)
            print(footFitJointsGlobal)
            cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
        elif attr == 18:
            print("checking otherTypeAttr")
            otherTypeAttr = cmds.getAttr(joint+".otherType")
            print(otherTypeAttr)
            if otherTypeAttr.startswith("Mid"):
                midFitJointGlobal.append(joint)
                print(midFitJointGlobal)
            elif otherTypeAttr.startswith("Eye"):
                eyeFitJointsGlobal.append(joint)
                print(eyeFitJointsGlobal)
            elif otherTypeAttr.startswith("Chest"):
                chestFitJointsGlobal.append(joint)
                print(chestFitJointsGlobal)
                cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
            elif otherTypeAttr.startswith("Hip"):
                firstLegFitJointsGlobal.append(joint)
                print(firstLegFitJointsGlobal)
                cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
            elif otherTypeAttr.startswith("Toes") and not otherTypeAttr.startswith("ToesEnd"):
                toesFitJointGlobal.append(joint)
                print(toesFitJointGlobal)
            elif otherTypeAttr.startswith("BigToe"):
                bigToeFitJointsGlobal.append(joint)
                print(bigToeFitJointsGlobal)
            elif otherTypeAttr.startswith("PinkyToe"):
                pinkyToeFitJointsGlobal.append(joint)
                print(pinkyToeFitJointsGlobal)
            elif otherTypeAttr.startswith("Shoulder"):
                firstArmFitJointsGlobal.append(joint)
                print(firstArmFitJointsGlobal)
                cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
            elif otherTypeAttr.startswith("Hand"):
                handFitJointsGlobal.append(joint)
                print(handFitJointsGlobal)
                cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
            elif otherTypeAttr.startswith("Foot"):
                footFitJointsGlobal.append(joint)
                print(footFitJointsGlobal)
                cmds.setAttr(joint + ".drawLabel", previousDrawLabelStatus)
            elif otherTypeAttr.startswith("0"):
                firstIKSplineFitJointsGlobal.append(joint)
                print(firstIKSplineFitJointsGlobal)
            elif otherTypeAttr.startswith("ToesEnd"):
                toesEndFitJointsGlobal.append(joint)
                print(toesEndFitJointsGlobal)
            elif otherTypeAttr.startswith("Heel"):
                heelFitJointsGlobal.append(joint)
                print(heelFitJointsGlobal)
            elif otherTypeAttr.startswith("QToes"):
                qToesFitJointGlobal.append(joint)
            elif otherTypeAttr.startswith("Root"):
                firstMiddleFitJointsGlobal.append(joint)

# find End joints to skip them later
def findEndJoints(allFitJoints):
    global endJointsList
    # reset for safe
    endJointsList = []

    # need to skip end joints with joint label: Hand, Foot

    for joint in allFitJoints:
        if not cmds.listRelatives(joint, children=1):
            # this one is end joint
            # double check ik label

            endJointsList.append(joint)
    print(endJointsList)
    return endJointsList

def filterOutListOfJoints(jointList, needToRemoveJointList):
    # new joint list with no end joints
    newJointList = []
    for joint in jointList:
        if joint in needToRemoveJointList:
            pass
        else:
            newJointList.append(joint)
    return newJointList

def filterGlobalList_from_GlobalList(keptGlobalList, removeGlobalList):
    # filter out face joints from ikSpline
    if keptGlobalList and removeGlobalList:
        allRemoveGlobalList = []
        for removeList in removeGlobalList:
            allRemoveGlobalList.extend(removeList)

        newKeptGlobalList = []

        for keptList in keptGlobalList:
            keptList = filterOutListOfJoints(keptList, allRemoveGlobalList)
            newKeptGlobalList.append(keptList)
        return newKeptGlobalList

def findHeadFitJoint():
    global eyeFitJointsGlobal
    global middleFitJoints
    global headFitJointsGlobal

    headFitJointsGlobal = []
    headListSearch = cmds.ls("Head*")

    if eyeFitJointsGlobal:
        for eyeFitJoint in eyeFitJointsGlobal:
            headFitJoint = cmds.listRelatives(eyeFitJoint, parent=1)[0]
            headFitJointsGlobal.append(headFitJoint)
        print(headFitJointsGlobal)
        return headFitJointsGlobal

    # if cannot search based on Eye label then search by name (hard code)
    elif headListSearch:
        for headJoint in headListSearch:
            if cmds.nodeType(headJoint) == 'joint':
                headFitJointsGlobal.append(headJoint)
        if headFitJointsGlobal:
            return headFitJointsGlobal

# need to look for ikSpline Fit joints first, to remove them from Mid (torso) joints later
def findIKSplineJointList():
    global firstIKSplineFitJointsGlobal
    global iKSplineFitJointsGlobal
    global endJointsList

    iKSplineFitJointsGlobal = []
    if endJointsList and firstIKSplineFitJointsGlobal:
        for joint in endJointsList:
            drawLabelStatus = cmds.getAttr(joint+".drawLabel")
            if drawLabelStatus:
                jointLabel = cmds.getAttr(joint + ".otherType")
                numList = [int(s) for s in jointLabel.split() if s.isdigit()]
                if numList:

                    allJointParents = cmds.ls(joint, long=True)[0].split('|')[1:-1]
                    allJointParents.reverse()
                    iKSplineFitJoints = []
                    for parentJoint in allJointParents:
                        if parentJoint in firstIKSplineFitJointsGlobal:
                            iKSplineFitJoints.insert(0, parentJoint)
                            break
                        else:
                            iKSplineFitJoints.insert(0, parentJoint)
                    iKSplineFitJointsGlobal.append(iKSplineFitJoints)
    else:
        iKSplineFitJointsGlobal = [[]]
    print(iKSplineFitJointsGlobal)
    return iKSplineFitJointsGlobal

def updateLockMiddle():
    if cmds.objExists("Root"):
        if cmds.getAttr("Root.tx", lock=1):
            mel.eval('asFitModeLockCenterJoints')
            if not cmds.getAttr("Root.tx", lock=1):
                print("middle joints are unlocked now. Now lock them again")
                mel.eval('asFitModeLockCenterJoints')
        else:
            print("middle joints are not locked. Lock them now")
            mel.eval('asFitModeLockCenterJoints')

def findMiddleJointList(allFitJoints):
    # turn lock middle off and back on to update lock middle status
    updateLockMiddle()

    global middleFitJoints
    global endJointsList

    lockedJointsListAll = []
    middleFitJoints = []

    for joint in allFitJoints:
        rxLockStatus = cmds.getAttr(joint+".rx", lock=1)
        ryLockStatus = cmds.getAttr(joint+".ry", lock=1)
        if rxLockStatus and ryLockStatus and joint not in lockedJointsListAll:
            lockedJointsListAll.append(joint)

    # filter out end joints to have middleFitJoints.
    if endJointsList:
        middleFitJoints = filterOutListOfJoints(lockedJointsListAll, endJointsList)

    print(middleFitJoints)
    return middleFitJoints

def findTorsoFitJoints():
    global chestFitJointsGlobal
    global torsoFitJoints
    torsoFitJoints = []
    if chestFitJointsGlobal:
        # should only one Chest joint
        torsoFitJoints.append(chestFitJointsGlobal[0])
        allChestFitJointParents = cmds.ls(chestFitJointsGlobal[0], long=True)[0].split('|')[1:-1]
        allChestFitJointParents.reverse()
        for joint in allChestFitJointParents:
            if joint == "FitSkeleton":
                break
            else:
                torsoFitJoints.insert(0, joint)
    print(torsoFitJoints)
    return(torsoFitJoints)


# How to find endJoint for ikSpline?
def findEndIKLabeledFitJoint(firstFitJoint):
    global firstArmFitJointsGlobal
    global handFitJointsGlobal

    global firstLegFitJointsGlobal
    global toesFitJointGlobal
    global qToesFitJointGlobal

    if firstArmFitJointsGlobal and handFitJointsGlobal:
        if firstFitJoint in firstArmFitJointsGlobal:
            firstJointChildList = cmds.listRelatives(firstFitJoint, children=1, allDescendents=1)
            for handJoint in handFitJointsGlobal:
                if handJoint in firstJointChildList:
                    print(handJoint)
                    return handJoint

    if firstLegFitJointsGlobal and toesFitJointGlobal:
        if firstFitJoint in firstLegFitJointsGlobal:
            firstJointChildList = cmds.listRelatives(firstFitJoint, children=1, allDescendents=1)
            print(firstJointChildList)
            for toeJoint in toesFitJointGlobal:
                if toeJoint in firstJointChildList:
                    print(toeJoint)
                    return toeJoint

    if firstLegFitJointsGlobal and qToesFitJointGlobal:
        if firstFitJoint in firstLegFitJointsGlobal:
            firstJointChildList = cmds.listRelatives(firstFitJoint, children=1, allDescendents=1)
            print(firstJointChildList)
            for qToeJoint in qToesFitJointGlobal:
                if qToeJoint in firstJointChildList:
                    print(qToeJoint)
                    return qToeJoint
    print("Cannot find end joint")
    return None

# functions to find child joint list based first IK label joints lists.
def findBranchJointList(firstFitJoint):
    # does not apply for middle joints (already have function above)
    global endJointsList

    if not firstFitJoint:
        raise Exception("first fit joint does not exist")

    branchJointList = []

    allChildJoints = cmds.listRelatives(firstFitJoint, children=1, allDescendents=1)
    if allChildJoints:
        # need to test sort
        allChildJoints.reverse()

        definedEndFitJoint = findEndIKLabeledFitJoint(firstFitJoint)

        # for toes, fingers, tails
        if not definedEndFitJoint:
            for joint in allChildJoints:
                if joint not in endJointsList:
                    branchJointList.append(joint)
            branchJointList.insert(0, firstFitJoint)
            print(branchJointList)
            return branchJointList
        else:
            for joint in allChildJoints:
                if joint not in endJointsList:
                    if joint != definedEndFitJoint:
                        branchJointList.append(joint)
                    else:
                        branchJointList.append(definedEndFitJoint)
                        break
            branchJointList.insert(0, firstFitJoint)
            print(branchJointList)
            return branchJointList
    else:
        print("This "+firstFitJoint+" have no children joints")
        return None

# in case of Hip >> pelvis/ legAim & Shoulder >> scapular/ clavicle. Add them to the current list if having.
def updateFirstJointIn_Arm_and_Leg_FitJointsList(jointListGlobal):
    global torsoFitJoints

    upperJointList = []
    for jointList in jointListGlobal:
        upperJoint = cmds.listRelatives(jointList[0], parent=1)[0]
        if upperJoint not in torsoFitJoints and upperJoint not in upperJointList:
            jointList.insert(0, upperJoint)
            upperJointList.append(upperJoint)
    print(jointListGlobal)
    return jointListGlobal

def findFaceItemsFitJointsGlobal():
    global chestFitJointsGlobal
    global armFitJointsGlobal
    global headFitJointsGlobal
    global faceItemsFitJointsGlobal
    global iKSplineFitJointsGlobal

    faceItemsFitJointsGlobal = []
    # if having head >> find head children & find neck until reach Chest. Filter out end joints.
    # filter out ikSplines from the list. Just to make sure.
    if headFitJointsGlobal:
        for headFitJoint in headFitJointsGlobal:
            # find children
            faceItems = findBranchJointList(headFitJoint)

            if faceItems:
                # find necks
                allHeadFitJointParents = cmds.ls(headFitJoint, long=True)[0].split('|')[1:-1]
                allHeadFitJointParents.reverse()
                for parentJoint in allHeadFitJointParents:
                    if parentJoint in chestFitJointsGlobal or parentJoint == "FitSkeleton":
                        break
                    else:
                        faceItems.insert(0, parentJoint)

                faceItemsFitJointsGlobal.append(faceItems)

        if iKSplineFitJointsGlobal and faceItemsFitJointsGlobal:
            faceItemsFitJointsGlobal = filterGlobalList_from_GlobalList(faceItemsFitJointsGlobal, iKSplineFitJointsGlobal)
        print(faceItemsFitJointsGlobal)
        return faceItemsFitJointsGlobal


    # Else find Chest children, skip armFitJointsGlobal.
    # Filter out end joints using findBranchJointList.
    # filter out ikSplines from the list. Just to make sure
    elif chestFitJointsGlobal:
        chestChildren = cmds.listRelatives(chestFitJointsGlobal[0], children=1)
        for child in chestChildren:
            if child in armFitJointsGlobal:
                pass
            else:
                faceItems = findBranchJointList(child)
                if faceItems:
                    faceItemsFitJointsGlobal.append(faceItems)

                if iKSplineFitJointsGlobal and faceItemsFitJointsGlobal:
                    faceItemsFitJointsGlobal = filterGlobalList_from_GlobalList(faceItemsFitJointsGlobal, iKSplineFitJointsGlobal)
                print(faceItemsFitJointsGlobal)
                return faceItemsFitJointsGlobal

def flattenGlobalList(fitJointsGlobal):
    flattenList = []
    for fitJoints in fitJointsGlobal:
        flattenList.extend(fitJoints)
    return flattenList

def findFKFitJointsGlobal():
    global fKFitJointsGlobal
    fKFitJointsGlobal = []
    global endJointsList
    global torsoFitJoints

    global faceItemsFitJointsGlobal
    global iKSplineFitJointsGlobal
    global armFitJointsGlobal
    global fingersFitJointsGlobal
    global legFitJointsGlobal
    global toesIndividualFitJointsGlobal

    needToCheckList = []

    if torsoFitJoints:
        needToCheckList.extend(torsoFitJoints)
    if faceItemsFitJointsGlobal[0]:
        needToCheckList.extend(flattenGlobalList(faceItemsFitJointsGlobal))
    if iKSplineFitJointsGlobal[0]:
        needToCheckList.extend(flattenGlobalList(iKSplineFitJointsGlobal))
    if armFitJointsGlobal[0]:
        needToCheckList.extend(flattenGlobalList(armFitJointsGlobal))
    if fingersFitJointsGlobal[0]:
        needToCheckList.extend(flattenGlobalList(fingersFitJointsGlobal))
    if legFitJointsGlobal[0]:
        needToCheckList.extend(flattenGlobalList(legFitJointsGlobal))
    if toesIndividualFitJointsGlobal[0]:
        needToCheckList.extend(flattenGlobalList(toesIndividualFitJointsGlobal))

    for endJoint in endJointsList:
        allEndJointParents = cmds.ls(endJoint, long=True)[0].split('|')[1:-1]
        if allEndJointParents:
            allEndJointParents.reverse()
            fkFitJoints = []
            for parentJoint in allEndJointParents:
                if parentJoint in needToCheckList:
                    break
                else:
                    fkFitJoints.insert(0, parentJoint)

            if fkFitJoints:
                needToCheckList.extend(fkFitJoints)
                fKFitJointsGlobal.append(fkFitJoints)
                print(fKFitJointsGlobal)
    return fKFitJointsGlobal

# try to turn all label >> get variables >> return them back.
# need function for all missing branche (FK) >> test bird rig
# and remove FK branches from all the current Global List (dragon rig)
# check bug: no leg, no face items
# check dinosaur: missing fk arm, missing head (but still having eyes)
# check fish: missing torso joints & fk joints
# vehicle: failed
def findAllImportantJoints_and_ChildJointsLists():
    global endJointsList
    endJointsList = []
    global firstMiddleFitJointsGlobal
    firstMiddleFitJointsGlobal = []
    global firstArmFitJointsGlobal
    firstArmFitJointsGlobal = []
    global firstLegFitJointsGlobal
    firstLegFitJointsGlobal = []
    global firstIKSplineFitJointsGlobal
    firstIKSplineFitJointsGlobal = []

    global toesFitJointGlobal
    toesFitJointGlobal = []
    global bigToeFitJointsGlobal
    bigToeFitJointsGlobal = []
    global pinkyToeFitJointsGlobal
    pinkyToeFitJointsGlobal = []
    global toesEndFitJointsGlobal
    toesEndFitJointsGlobal = []
    global heelFitJointsGlobal
    heelFitJointsGlobal = []
    global shoulderFitJointGlobal
    shoulderFitJointGlobal = []
    global footFitJointsGlobal
    footFitJointsGlobal = []
    global eyeFitJointsGlobal
    eyeFitJointsGlobal = []
    global chestFitJointsGlobal
    chestFitJointsGlobal = []
    global headFitJointsGlobal
    headFitJointsGlobal = []

    global middleFitJoints
    middleFitJoints = []
    global torsoFitJoints
    torsoFitJoints = []
    global legFitJointsGlobal
    legFitJointsGlobal = []
    global armFitJointsGlobal
    armFitJointsGlobal = []
    global fingersFitJointsGlobal
    fingersFitJointsGlobal = []
    global iKSplineFitJointsGlobal
    iKSplineFitJointsGlobal = []

    global toesIndividualFitJointsGlobal
    toesIndividualFitJointsGlobal = []

    global qToesFitJointGlobal
    qToesFitJointGlobal = []

    global faceItemsFitJointsGlobal
    faceItemsFitJointsGlobal = []

    global handFitJointsGlobal
    handFitJointsGlobal = []

    global fKFitJointsGlobal
    fKFitJointsGlobal = []

    global allFitJoints
    allFitJoints = []

    # auto rename any object have the same name
    autoRenamingDuplicateObjects()

    allJoints = cmds.ls(type="joint")
    allFitSkeletonChildren = cmds.listRelatives("FitSkeleton", children=1, ad=1)
    for item in allFitSkeletonChildren:
        if item in allJoints:
            allFitJoints.append(item)

    # loop to find end joints
    findEndJoints(allFitJoints)

    # loop again to IK labeled joints
    for joint in allFitJoints:
        findIKLabelJoint(joint)

    # get ik spline fit joints
    findIKSplineJointList()
    print(iKSplineFitJointsGlobal)

    # get head joints based on ik eyes or actual joint names
    findHeadFitJoint()

    # get middle fit joints and torso fit joints
    findMiddleJointList(allFitJoints)

    # find torso fit joints (stop at Chest joint)
    findTorsoFitJoints()

    print(firstLegFitJointsGlobal)
    # get leg Fit joints (multiple list)
    legFitJointsGlobal = []
    if firstLegFitJointsGlobal:
        for firstLegFitJoint in firstLegFitJointsGlobal:
            legFitJoints = findBranchJointList(firstLegFitJoint)
            if legFitJoints:
                legFitJointsGlobal.append(legFitJoints)
    print(legFitJointsGlobal)

    if not legFitJointsGlobal:
        legFitJointsGlobal = [[]]

    if all(legFitJointsGlobal):
        updateFirstJointIn_Arm_and_Leg_FitJointsList(legFitJointsGlobal)

    # get arm Fit joints (multiple list)
    armFitJointsGlobal = []
    if firstArmFitJointsGlobal:
        for firstArmFitJoint in firstArmFitJointsGlobal:
            armFitJoints = findBranchJointList(firstArmFitJoint)
            if armFitJoints:
                armFitJointsGlobal.append(armFitJoints)
    print(armFitJointsGlobal)
    if not armFitJointsGlobal:
        armFitJointsGlobal = [[]]
    if all(armFitJointsGlobal):
        updateFirstJointIn_Arm_and_Leg_FitJointsList(armFitJointsGlobal)

    # get finger joints
    fingersFitJointsGlobal = []
    if handFitJointsGlobal:
        for handFitJoint in handFitJointsGlobal:
            fingerFitJoints = findBranchJointList(handFitJoint)
            if fingerFitJoints:
                fingersFitJointsGlobal.append(fingerFitJoints)
                # need to remove the wrist joint
                fingerFitJoints.remove(handFitJoint)

    if not fingersFitJointsGlobal:
        fingersFitJointsGlobal = [[]]

    # get toe joints
    toesIndividualFitJointsGlobal = []
    if toesFitJointGlobal:
        for toesFitJoint in toesFitJointGlobal:
            toesIndividualFitJoints = findBranchJointList(toesFitJoint)
            if toesIndividualFitJoints:
                toesIndividualFitJointsGlobal.append(toesIndividualFitJoints)
                # need to remove the Toe master joint
                toesIndividualFitJoints.remove(toesFitJoint)

    # get qToes' toe joints
    if qToesFitJointGlobal:
        for qToesFitJoint in qToesFitJointGlobal:
            toesIndividualFitJoints = findBranchJointList(qToesFitJoint)
            if toesIndividualFitJoints:
                toesIndividualFitJointsGlobal.append(toesIndividualFitJoints)
                # need to remove the Toe master joint
                toesIndividualFitJoints.remove(qToesFitJoint)

    if not toesIndividualFitJointsGlobal:
        toesIndividualFitJointsGlobal = [[]]
    print(toesIndividualFitJointsGlobal)


    # then get face items (if having)
    findFaceItemsFitJointsGlobal()

    # find fk chains when everything is done
    fKFitJointsGlobal = findFKFitJointsGlobal()
    if not fKFitJointsGlobal:
        fKFitJointsGlobal = [[]]

########################################
# Start working with Fit Skeleton here #
########################################

def highestY_in_FitSkeleton():
    maxY = 0
    if not cmds.objExists("FitSkeleton"):
        raise Exception("Fit Skeleton doesn't not exist for highestJoint function to work")
    else:
        allJoints = cmds.ls(type="joint")
        for joint in allJoints:
            jointHeight = cmds.xform(joint, q=1, t=1, ws=1)[1]
            if jointHeight >= maxY:
                maxY = jointHeight
    print(maxY)
    return maxY

# count BBox from y = 0
def getOriginalBodyMeshesSize(originalBodyMeshes):
    global meshesSize
    meshesSize = []
    if not originalBodyMeshes:
        raise Exception("No body mesh for bounding box calculation")
    else:

        if len(originalBodyMeshes) > 1:
            dupOriginalBodyMeshes = cmds.duplicate(originalBodyMeshes)
            measureMesh = cmds.polyUnite(dupOriginalBodyMeshes, name="body_merged_to_measure", ch=0)[0]

            maxXMesh = cmds.exactWorldBoundingBox(measureMesh)[3]
            minXMesh = cmds.exactWorldBoundingBox(measureMesh)[0]
            xSize = maxXMesh - minXMesh

            maxYMesh = cmds.exactWorldBoundingBox(measureMesh)[4]
            minYMesh = cmds.exactWorldBoundingBox(measureMesh)[1]
            ySize = maxYMesh + minYMesh

            maxZMesh = cmds.exactWorldBoundingBox(measureMesh)[5]
            minZMesh = cmds.exactWorldBoundingBox(measureMesh)[2]
            zSize = maxZMesh - minZMesh

            meshesSize = [xSize, ySize, zSize]

            cmds.delete(measureMesh)
            return meshesSize

        elif len(originalBodyMeshes) == 1:

            maxXMesh = cmds.exactWorldBoundingBox(originalBodyMeshes[0])[3]
            minXMesh = cmds.exactWorldBoundingBox(originalBodyMeshes[0])[0]
            xSize = maxXMesh - minXMesh

            maxYMesh = cmds.exactWorldBoundingBox(originalBodyMeshes[0])[4]
            minYMesh = cmds.exactWorldBoundingBox(originalBodyMeshes[0])[1]
            ySize = maxYMesh + minYMesh

            maxZMesh = cmds.exactWorldBoundingBox(originalBodyMeshes[0])[5]
            minZMesh = cmds.exactWorldBoundingBox(originalBodyMeshes[0])[2]
            zSize = maxZMesh - minZMesh

            meshesSize = [xSize, ySize, zSize]

            return meshesSize

####################################################
# Structure, Meshes preparing, update Fit Skeleton #
####################################################
def createCutMesh(originalBodyMeshes):
    if len(originalBodyMeshes) > 1:
        meshes = cmds.duplicate(originalBodyMeshes)
        cutMesh = cmds.polyUnite(meshes, ch=0, name="bodyMeshesMerged_Cut")[0]
        if cmds.objExists(cutMesh):
            cmds.parent(cutMesh, "dupMeshesForCut_Grp")
            print(cutMesh)

    elif len(originalBodyMeshes) == 1:
        if not cmds.objExists(originalBodyMeshes[0]+"_Cut"):
            cutMesh = cmds.duplicate(originalBodyMeshes[0], name=originalBodyMeshes[0] + "_Cut")
            cmds.parent(cutMesh, "dupMeshesForCut_Grp")
            print(cutMesh)

def createStructure(originalBodyMeshes=None, deformedProps=None, nonDeformedProps=None, faceItems=None):
    if not cmds.objExists("TRCR_Grp"):
        cmds.group(name="TRCR_Grp", em=1)
    if not cmds.objExists("dupMeshesForCut_Grp"):
        cmds.group(name="dupMeshesForCut_Grp", em=1)
        cmds.parent("dupMeshesForCut_Grp", "TRCR_Grp")
        cmds.hide("dupMeshesForCut_Grp")
    if not cmds.objExists("deformJointMeshes_Grp"):
        cmds.group(name="deformJointMeshes_Grp", em=1)
        cmds.parent("deformJointMeshes_Grp", "TRCR_Grp")
        cmds.hide("deformJointMeshes_Grp")
    if not cmds.objExists("originalBodyMeshes_Grp"):
        cmds.group(name="originalBodyMeshes_Grp", em=1)
        cmds.parent("originalBodyMeshes_Grp", "TRCR_Grp")
        cmds.hide("originalBodyMeshes_Grp")
    if not cmds.objExists("deformedProps_Grp"):
        cmds.group(name="deformedProps_Grp", em=1)
        cmds.parent("deformedProps_Grp", "TRCR_Grp")
        cmds.hide("deformedProps_Grp")
    if not cmds.objExists("nonDeformedProps_Grp"):
        cmds.group(name="nonDeformedProps_Grp", em=1)
        cmds.parent("nonDeformedProps_Grp", "TRCR_Grp")
        cmds.hide("nonDeformedProps_Grp")
    if not cmds.objExists("faceItems_Grp"):
        cmds.group(name="faceItems_Grp", em=1)
        cmds.parent("faceItems_Grp", "TRCR_Grp")
        cmds.hide("faceItems_Grp")
    if not cmds.objExists("curveTemplates_Grp"):
        cmds.group(name="curveTemplates_Grp", em=1)
        cmds.parent("curveTemplates_Grp", "TRCR_Grp")
        cmds.hide("curveTemplates_Grp")
    if not cmds.objExists("eyesLocator_Grp"):
        cmds.group(name="eyesLocator_Grp", em=1)
        cmds.parent("eyesLocator_Grp", "TRCR_Grp")

    # this is for auto load meshes later

    if originalBodyMeshes:
        cmds.parent(originalBodyMeshes, "originalBodyMeshes_Grp")
        createCutMesh(originalBodyMeshes)

    if deformedProps:
        cmds.parent(deformedProps, "deformedProps_Grp")

    if nonDeformedProps:
        cmds.parent(nonDeformedProps, "nonDeformedProps_Grp")

    if faceItems:
        for faceItem in faceItems:
            try:
                cmds.parent(faceItem, "originalBodyMeshes_Grp")
            except:
                print("already parent faceItem under faceItems_Grp")
            if cmds.objExists(faceItem+"_Cut"):
                cmds.delete(faceItem+"_Cut")
            dupFaceItem = cmds.duplicate(faceItem, name=faceItem+"_Cut")[0]
            cmds.parent(dupFaceItem, "faceItems_Grp")
    cmds.select(clear=1)

# Duplicate main mesh >> ready to be cut mesh (cut mesh in short). Then hide main mesh.
# If multiple main meshes >> combine them first then make cut mesh
# With face meshes >> how?

# use this to load meshes into variables when there is TRCR_Grp
def autoLoadMeshesVariable():
    global originalBodyMeshes
    global deformedProps
    global nonDeformedProps
    global faceItems

    # double check structure and all the meshes as well. If structure >> reset and add all meshes again
    # check if the group is already exists. Then create structure one more time to create missing folders.
    # Else, dont create anything
    if cmds.objExists("TRCR_Grp"):
        createStructure(None, None, None, None)
        originalBodyMeshes = []
        deformedProps = []
        nonDeformedProps = []
        originalBodyMeshes = cmds.listRelatives("originalBodyMeshes_Grp", children=1)
        if not originalBodyMeshes:
            originalBodyMeshes = []
        print(originalBodyMeshes)
        deformedProps = cmds.listRelatives("deformedProps_Grp", children=1)
        if not deformedProps:
            deformedProps = []
        print(deformedProps)
        nonDeformedProps = cmds.listRelatives("nonDeformedProps_Grp", children=1)
        if not nonDeformedProps:
            nonDeformedProps = []
        print(nonDeformedProps)
        faceItems = cmds.listRelatives("faceItems_Grp", children=1)
        if not faceItems:
            faceItems = []
        print(faceItems)

#################################
# custom eye fit joint location #
#################################
def setEyeCenterLoop():
    global eyeCenterLoc
    global eyeCenterLocTF
    global eyeFitJointsGlobal
    global meshesSize

    if eyeFitJointsGlobal:
        for eyeFitJoint in eyeFitJointsGlobal:
            locatorName = eyeFitJoint + "_Center_Locator"
            if cmds.objExists(locatorName):
                pass
            else:
                currentSelection = cmds.ls(sl=1)
                if currentSelection:
                    cmds.setToolTo("Move")
                    centerPos = cmds.manipMoveContext("Move", q=1, p=1)
                    eyeCenterLoc = cmds.spaceLocator(a=1, name=eyeFitJoint + "_Center_Locator", p=centerPos)
                    cmds.xform(eyeCenterLoc, cp=1)

                    if meshesSize:
                        locShape = cmds.listRelatives(eyeCenterLoc, children=1, shapes=1)[0]
                        cmds.setAttr(locShape+".localScaleX", meshesSize[1] / 10)
                        cmds.setAttr(locShape + ".localScaleY", meshesSize[1] / 10)
                        cmds.setAttr(locShape + ".localScaleZ", meshesSize[1] / 10)

                    cmds.parent(eyeFitJoint + "_Center_Locator", "eyesLocator_Grp")
                    load_selected_as(eyeCenterLoc, eyeCenterLocTF)
                    cmds.select(clear=1)

def placeEyeFitJointCustomLocation():
    global eyeFitJointsGlobal
    if eyeFitJointsGlobal:
        for eyeFitJoint in eyeFitJointsGlobal:
            if cmds.objExists(eyeFitJoint + "_Center_Locator"):
                locPos = cmds.xform(eyeFitJoint + "_Center_Locator", q=1, rp=1, ws=1)
                cmds.xform(eyeFitJoint, t=locPos, ws=1)

##########
# Layout #
##########
def createBuildTab(masterTabs):
    global toolWindowWidth
    global originalBodyMeshes

    currentTabsUnderMasterTabs = cmds.tabLayout(masterTabs, q=1, tabLabel=1)
    print(currentTabsUnderMasterTabs)
    if not "Build" in currentTabsUnderMasterTabs:
        buildTab = cmds.rowColumnLayout(numberOfColumns=1, p=masterTabs)
        cmds.text("\n Please fill all the tabs frist, then: \n", p=buildTab)
        cmds.button(label="One Click Solution", p=buildTab, command='doItAll()', width=toolWindowWidth)

        cmds.text("\n Or, steps:\n", p=buildTab)

        cmds.separator(w=toolWindowWidth, h=10, p=buildTab)
        set_eye_center_loop_row = cmds.rowLayout(p=buildTab, nc=4)
        cmds.text(" Optional: Right Eye center loop ", p=set_eye_center_loop_row, width=toolWindowWidth*0.4)
        cmds.button(label="Show Meshes", p=set_eye_center_loop_row, width=toolWindowWidth * 0.25,
                    command='displayDeformJointMeshes_Grp()')
        tf_eyeCenterLoop = cmds.textField(eyeCenterLocTF, w=toolWindowWidth * 0.25, h=20, p=set_eye_center_loop_row, ed=0)
        cmds.button(label=' >> ', width=toolWindowWidth * 0.1, align='right', p=set_eye_center_loop_row,
                    command='setEyeCenterLoop()')

        cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.button(label="Place Joints Into Places", p=buildTab, command='placeFitJointIntoPlace()', width=toolWindowWidth)
        sep3 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        # cmds.button(label="Fix Pole Vector", p=buildTab, command='fixPoleVector()', width=toolWindowWidth)
        # sep4 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        build_and_toggle_row = cmds.rowLayout(p=buildTab, nc=2)
        cmds.button(label="Build Advanced Skeleton", p=build_and_toggle_row, command='buildAdvancedSkeleton()', width=toolWindowWidth*0.7)
        cmds.button(label="Toggle Fit/Adv", p=build_and_toggle_row, command='toggleFitAdv()',
                    width=toolWindowWidth * 0.3)
        sep5 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.button(label="Adjust Control Curves", p=buildTab, command='adjustControlCurves()', width=toolWindowWidth)
        sep8 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)


        scale_curve_row = cmds.rowLayout(p=buildTab, nc=3)
        cmds.button(label="Smaller Control Curves", p=scale_curve_row, command='smallerControlCurves()',
                    width=toolWindowWidth/3)
        cmds.button(label="Bigger Control Curves", p=scale_curve_row, command='biggerControlCurves()',
                    width=toolWindowWidth / 3)
        cmds.button(label="Right > Left", p=scale_curve_row, command='rightToLeftControls()',
                    width=toolWindowWidth / 3)

        cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.button(label="Bind Skin to Meshes", p=buildTab, command='bindDeformJointMeshesToDeformJoints_then_CopySkin()', width=toolWindowWidth)
        sep6 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        set_smooth_time_row = cmds.rowLayout(p=buildTab, nc=5)
        cmds.text(" Set smooth times: ", p=set_smooth_time_row, width=toolWindowWidth*0.2)
        cmds.intField(smoothTimeField, ed=True, p=set_smooth_time_row, width=toolWindowWidth*0.1, changeCommand='setSmoothTime()')
        cmds.button(label="Relax Skin Weights", p=set_smooth_time_row, width=toolWindowWidth*0.25, command='smoothSkinning({}, {}, {})'.format('MllInterface', originalBodyMeshes, smoothTime))
        cmds.text(" Or ", p=set_smooth_time_row, width=toolWindowWidth*0.1)
        cmds.button(label="Launch ngSkin Tool", p=set_smooth_time_row, width=toolWindowWidth*0.35, command='lauchNgSkinTool()')

        sep7 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.button(label="Create Proxy Meshes", p=buildTab, command='createProxyRig()', width=toolWindowWidth)
        sep21 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.button(label="Auto Attach Deformed Props", p=buildTab, command='autoAttachDeformedProps()', width=toolWindowWidth)
        sep9 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        attachNonDeformedProps_row = cmds.rowLayout(p=buildTab, nc=4)
        cmds.button(label="Auto Attach Non-deformed Props", p=attachNonDeformedProps_row, command='autoAttachNonDeformedProps()', width=toolWindowWidth*0.4)
        cmds.button(label="Create Joints", p=attachNonDeformedProps_row, command='createJointsForNonDeformedProps()', width=toolWindowWidth*0.2)
        cmds.text(' Or ', p=attachNonDeformedProps_row, width=toolWindowWidth*0.1)
        cmds.button(label="Launch Attach Props Tool", p=attachNonDeformedProps_row,
                    command='show_AttachPropsToolUI(win_ID)', width=toolWindowWidth*0.3)

        sep10 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.button(label="Clean Up Everything", p=buildTab, command='cleanUpEverything()', width=toolWindowWidth)
        sep20 = cmds.separator(w=toolWindowWidth, h=10, p=buildTab)

        cmds.tabLayout(masterTabs, edit=1, tabLabel=(buildTab, "Build"))
        return buildTab

def createJointsGlobalTab(fitJointsGlobal):
    global masterTabs
    global toolWindowWidth

    toBeDeleteTabs = []

    if fitJointsGlobal == armFitJointsGlobal:
        name = "Arm"
    elif fitJointsGlobal == fingersFitJointsGlobal:
        name = "Fingers"
    elif fitJointsGlobal == legFitJointsGlobal:
        name = "Leg"
    elif fitJointsGlobal == toesIndividualFitJointsGlobal:
        name = "Toes"
    elif fitJointsGlobal == iKSplineFitJointsGlobal:
        name = "IKSpline"
    elif fitJointsGlobal == faceItemsFitJointsGlobal:
        name = "Face"
    elif fitJointsGlobal == fKFitJointsGlobal:
        name = "FK"

    global armAddButtonsGlobal
    global armCutButtonsGlobal
    global armClearButtonsGlobal

    global fingersAddButtonsGlobal
    global fingersCutButtonsGlobal
    global fingersClearButtonsGlobal

    global legAddButtonsGlobal
    global legCutButtonsGlobal
    global legClearButtonsGlobal

    global toesAddButtonsGlobal
    global toesCutButtonsGlobal
    global toesClearButtonsGlobal

    global faceAddButtonsGlobal
    global faceCutButtonsGlobal
    global faceClearButtonsGlobal

    global ikSplinesAddButtonsGlobal
    global ikSplinesCutButtonsGlobal
    global ikSplinesClearButtonsGlobal

    global fkAddButtonsGlobal
    global fkCutButtonsGlobal
    global fkClearButtonsGlobal

    # avoid fitJointsGlobal = []
    if fitJointsGlobal:
        print(fitJointsGlobal)
        # check all items have value
        if all(fitJointsGlobal):
            for fitJoints in fitJointsGlobal:
                print(fitJoints)
                addButtons = []
                cutButtons = []
                clearButtons = []

                print(fitJoints)
                indexNum = fitJointsGlobal.index(fitJoints)
                tabName = name+str(indexNum)
                print(tabName)
                currentTabsUnderMasterTabs = cmds.tabLayout(masterTabs, q=1, tabLabel=1)
                print(currentTabsUnderMasterTabs)
                if not tabName in currentTabsUnderMasterTabs:
                    tab = cmds.columnLayout(p=masterTabs)
                    toBeDeleteTabs.append(tab)

                    if fitJointsGlobal == faceItemsFitJointsGlobal:
                        cmds.separator(w=toolWindowWidth, h=10, p=tab)
                        displayFaceItemsRow = cmds.rowLayout(numberOfColumns=1, p=tab)
                        cmds.button(label="Toggle Face Items", p=displayFaceItemsRow, width=toolWindowWidth,
                                    command='displayFaceItems()')
                    cmds.separator(w=toolWindowWidth, h=10, p=tab)

                    for fitJoint in fitJoints:
                        row = cmds.rowLayout(numberOfColumns=4, p=tab)

                        cmds.text('{}'.format(fitJoint), width=toolWindowWidth * 0.7)
                        cut_btn = cmds.button(label=" >> ", p=row, width=toolWindowWidth * 0.1, bgc=[0, 0.4, 0],
                                    command='findSideThenCutFaces_toCreate_DeformJointMesh("{}")'.format(fitJoint))
                        cutButtons.append(cut_btn)
                        # print(cutButtons)

                        add_btn = cmds.button(label=" + ", p=row, width=toolWindowWidth * 0.1, bgc=[0, 0.4, 0],
                                    command='findSideThenAddDeformJointMesh("{}")'.format(fitJoint))
                        addButtons.append(add_btn)
                        # print(addButtons)

                        clear_btn = cmds.button(label="X", p=row, width=toolWindowWidth * 0.1, bgc=[0, 0.4, 0],
                                    command='clearPairFromPairJointsMeshesGlobal("{}")'.format(fitJoint))
                        clearButtons.append(clear_btn)
                        # print(clearButtons)

                        row2 = cmds.rowLayout(numberOfColumns=1, p=tab)
                        cmds.separator(w=toolWindowWidth, h=10, p=row2)
                    cmds.tabLayout(masterTabs, edit=1, tabLabel=(tab, tabName))

                if addButtons and cutButtons and clearButtons and fitJointsGlobal == armFitJointsGlobal:
                    armAddButtonsGlobal.append(addButtons)
                    armCutButtonsGlobal.append(cutButtons)
                    armClearButtonsGlobal.append(clearButtons)
                if addButtons and cutButtons and clearButtons and fitJointsGlobal == fingersFitJointsGlobal:
                    fingersAddButtonsGlobal.append(addButtons)
                    fingersCutButtonsGlobal.append(cutButtons)
                    fingersClearButtonsGlobal.append(clearButtons)
                if addButtons and cutButtons and clearButtons and fitJointsGlobal == legFitJointsGlobal:
                    legAddButtonsGlobal.append(addButtons)
                    legCutButtonsGlobal.append(cutButtons)
                    legClearButtonsGlobal.append(clearButtons)
                if addButtons and cutButtons and clearButtons and fitJointsGlobal == toesIndividualFitJointsGlobal:
                    toesAddButtonsGlobal.append(addButtons)
                    toesCutButtonsGlobal.append(cutButtons)
                    toesClearButtonsGlobal.append(clearButtons)
                if addButtons and cutButtons and clearButtons and fitJointsGlobal == iKSplineFitJointsGlobal:
                    ikSplinesAddButtonsGlobal.append(addButtons)
                    ikSplinesCutButtonsGlobal.append(cutButtons)
                    ikSplinesClearButtonsGlobal.append(clearButtons)
                if addButtons and cutButtons and clearButtons and fitJointsGlobal == fKFitJointsGlobal:
                    fkAddButtonsGlobal.append(addButtons)
                    fkCutButtonsGlobal.append(cutButtons)
                    fkClearButtonsGlobal.append(clearButtons)
                if addButtons and cutButtons and clearButtons and fitJointsGlobal == faceItemsFitJointsGlobal:
                    faceAddButtonsGlobal.append(addButtons)
                    faceCutButtonsGlobal.append(cutButtons)
                    faceClearButtonsGlobal.append(clearButtons)
    return toBeDeleteTabs

def autoAdjustFitSkeletonHeight():
    global originalBodyMeshes
    global meshesSize
    if originalBodyMeshes:
        meshesSize = getOriginalBodyMeshesSize(originalBodyMeshes)

    # update FitSkeleton height based on model bounding box size
    if not cmds.objExists("Main"):
        if meshesSize:
            fitSkeletonSize = highestY_in_FitSkeleton()
            ratio = meshesSize[1] / fitSkeletonSize
            print(ratio)

            # scale FitSkeleton to fit model's height
            cmds.xform("FitSkeleton", scale=[ratio, ratio, ratio])

            allFitJoints = []

            allJoints = cmds.ls(type="joint")
            allFitSkeletonChildren = cmds.listRelatives("FitSkeleton", children=1, ad=1)
            for item in allFitSkeletonChildren:
                if item in allJoints:
                    allFitJoints.append(item)

            fitJoint_PathLength_List = []

            print(allFitJoints)
            for fitJoint in allFitJoints:
                path = cmds.ls(fitJoint, long=1)[0]
                pathSplit = path.split("|")
                pathLength = len(pathSplit)
                fitJoint_PathLength_List.append([fitJoint, pathLength])

            fitJoint_PathLength_List.sort(key=lambda i: i[1])
            # result {[fitJoint, pathLength]}
            print(fitJoint_PathLength_List)

            joint_parentJoint_pos_list = []

            for pairJointPathLength in fitJoint_PathLength_List:
                fitJointPos = cmds.xform(pairJointPathLength[0], q=1, t=1, ws=1)
                joint_parentJoint_pos_list.append((pairJointPathLength[0], fitJointPos))

            print(joint_parentJoint_pos_list)

            # scale FitSkeleton back to 1
            cmds.xform("FitSkeleton", scale=[1, 1, 1])

            # move fitJoint into place (from end joints to >> Root joint)
            for list in joint_parentJoint_pos_list:
                cmds.xform(list[0], t=list[1], ws=1)

            # turn on fit mode to update joint size
            mel.eval('asFitModeManualUpdate')

            # clear selection
            cmds.select(clear=1)

# The goal is to update UI based on current Fit Template. "Add or remove joints if you want then hit UPDATE"
# when checking for tab, need to check the content inside the global list, not just global list itself [[]]
def updateFitTemplate():
    if not cmds.objExists("FitSkeleton"):
        raise Exception("Fit Skeleton does not exist")

    # load all IKLabel joints and Joint Lists. This will rename duplicate objects as well.
    findAllImportantJoints_and_ChildJointsLists()

    # load mesh variables
    autoLoadMeshesVariable()

    # auto adjust Fit Skeleton height based on model's height
    # why meshSize is not available??
    autoAdjustFitSkeletonHeight()

    # Tabs based on fit skeleton variables
    # It can add more but not able to remove existing. How??
    global masterTabs
    global toolWindowWidth
    global toBeDeletedLayoutAll

    global torsoCutButtons
    torsoCutButtons = []
    global torsoAddButtons
    torsoAddButtons = []
    global torsoClearButtons
    torsoClearButtons = []


    if toBeDeletedLayoutAll:
        for layout in toBeDeletedLayoutAll:
            try:
                cmds.deleteUI(layout)
            except:
                print("Cannot find layout to delete")

    if not cmds.objExists('Main'):
        if torsoFitJoints:
            torsoTabName = "Torso"
            currentTabsUnderMasterTabs = cmds.tabLayout(masterTabs, q=1, tabLabel=1)
            if torsoTabName in currentTabsUnderMasterTabs:
                pass
            else:
                torsoTab = cmds.columnLayout(p=masterTabs)
                cmds.separator(w=toolWindowWidth, h=10, p=torsoTab)
                toBeDeletedLayoutAll.append(torsoTab)
                print(torsoTab)

                for fitJoint in torsoFitJoints:
                    rowName = fitJoint + "Row"
                    rowName = cmds.rowLayout(numberOfColumns=4, p=torsoTab)
                    cmds.text('{}'.format(fitJoint), width=toolWindowWidth*0.7)
                    cut_btn = cmds.button(label=" >> ", p=rowName, width=toolWindowWidth*0.1, bgc=[0, 0.4, 0], command='findSideThenCutFaces_toCreate_DeformJointMesh("{}")'.format(fitJoint))
                    torsoCutButtons.append(cut_btn)
                    add_btn = cmds.button(label=" + ", p=rowName, width=toolWindowWidth*0.1, bgc=[0, 0.4, 0], command='findSideThenAddDeformJointMesh("{}")'.format(fitJoint))
                    torsoAddButtons.append(add_btn)
                    clear_btn = cmds.button(label="X", p=rowName, width=toolWindowWidth * 0.1, bgc=[0, 0.4, 0], command='clearPairFromPairJointsMeshesGlobal("{}")'.format(fitJoint))
                    torsoClearButtons.append(clear_btn)
                    rowName2 = cmds.rowLayout(numberOfColumns=1, p=torsoTab)
                    cmds.separator(w=toolWindowWidth, h=10, p=rowName2)
                cmds.tabLayout(masterTabs, edit=1, tabLabel=(torsoTab, 'Torso'))
        # reset all buttons global here
        global armAddButtonsGlobal
        armAddButtonsGlobal = []
        global armCutButtonsGlobal
        armCutButtonsGlobal = []
        global armClearButtonsGlobal
        armClearButtonsGlobal = []

        global fingersAddButtonsGlobal
        fingersAddButtonsGlobal = []
        global fingersCutButtonsGlobal
        fingersCutButtonsGlobal = []
        global fingersClearButtonsGlobal
        fingersClearButtonsGlobal = []

        global legAddButtonsGlobal
        legAddButtonsGlobal =[]
        global legCutButtonsGlobal
        legCutButtonsGlobal =[]
        global legClearButtonsGlobal
        legClearButtonsGlobal =[]

        global toesAddButtonsGlobal
        toesAddButtonsGlobal = []
        global toesCutButtonsGlobal
        toesCutButtonsGlobal =[]
        global toesClearButtonsGlobal
        toesClearButtonsGlobal =[]

        global faceAddButtonsGlobal
        faceAddButtonsGlobal = []
        global faceCutButtonsGlobal
        faceCutButtonsGlobal = []
        global faceClearButtonsGlobal
        faceClearButtonsGlobal = []

        global ikSplinesAddButtonsGlobal
        ikSplinesAddButtonsGlobal = []
        global ikSplinesCutButtonsGlobal
        ikSplinesCutButtonsGlobal = []
        global ikSplinesClearButtonsGlobal
        ikSplinesClearButtonsGlobal = []

        global fkAddButtonsGlobal
        fkAddButtonsGlobal = []
        global fkCutButtonsGlobal
        fkCutButtonsGlobal = []
        global fkClearButtonsGlobal
        fkClearButtonsGlobal = []

        global armFitJointsGlobal
        toBeDeletedLayoutArms = createJointsGlobalTab(armFitJointsGlobal)
        if toBeDeletedLayoutArms:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutArms)

        global fingersFitJointsGlobal
        toBeDeletedLayoutFingers = createJointsGlobalTab(fingersFitJointsGlobal)
        if toBeDeletedLayoutFingers:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutFingers)

        global legFitJointsGlobal
        toBeDeletedLayoutLeg = createJointsGlobalTab(legFitJointsGlobal)
        if toBeDeletedLayoutLeg:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutLeg)

        global toesIndividualFitJointsGlobal
        toBeDeletedLayoutToes = createJointsGlobalTab(toesIndividualFitJointsGlobal)
        if toBeDeletedLayoutToes:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutToes)

        global iKSplineFitJointsGlobal
        toBeDeletedLayoutIKSplines = createJointsGlobalTab(iKSplineFitJointsGlobal)
        if toBeDeletedLayoutIKSplines:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutIKSplines)

        global faceItemsFitJointsGlobal
        toBeDeletedLayoutFaceItems = createJointsGlobalTab(faceItemsFitJointsGlobal)
        if toBeDeletedLayoutFaceItems:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutFaceItems)

        global fKFitJointsGlobal
        toBeDeletedLayoutFK = createJointsGlobalTab(fKFitJointsGlobal)
        if toBeDeletedLayoutFK:
            toBeDeletedLayoutAll.extend(toBeDeletedLayoutFK)

    toBeDeletedLayoutBuild = createBuildTab(masterTabs)
    if toBeDeletedLayoutBuild:
        toBeDeletedLayoutAll.append(toBeDeletedLayoutBuild)

    # need to run auto load pairJointeMeshesGlobal
    autoReloadPairJointsMeshesGlobal()

    # auto adjust joint size
    autoAdjustJointSize()

def addAdvancedSkeletonPathToFitSkeleton(AdvancedSkeletonPath):
    if AdvancedSkeletonPath and cmds.objExists("FitSkeleton"):
        fitSkeletonShape = None
        fitSkeletonShape = cmds.listRelatives("FitSkeleton", children=1, shapes=1)[0]

        attrExist = cmds.attributeQuery("AdvancedSkeletonPath", node=fitSkeletonShape, exists=True)
        if attrExist:
            print("AdvancedSkeletonPath attribute already exists")
        else:
            cmds.addAttr(fitSkeletonShape, longName="AdvancedSkeletonPath", dt='string')
            cmds.setAttr(fitSkeletonShape+".AdvancedSkeletonPath", AdvancedSkeletonPath, type="string")

# import template
def importFitTemplate():
    global fitFileOptionMenu
    global fitSkeletonsDir

    if cmds.objExists("FitSkeleton"):
        cmds.delete("FitSkeleton")

    selectedFitFile = cmds.optionMenu(fitFileOptionMenu, q=1, v=1)
    print(selectedFitFile)

    if not fitSkeletonsDir:
        raise Exception("fitSkeletonsDir was not defined")

    fitFileFullPath = fitSkeletonsDir + selectedFitFile
    print(fitFileFullPath)

    cmds.file(fitFileFullPath, i=1)

    # turn on xray for all viewport panel
    panelList = cmds.getPanel(type='modelPanel')
    for panel in panelList:
        cmds.modelEditor(panel, e=1, jointXray=1)

    # need to run update fit template here as well
    updateFitTemplate()

    # add Adv Skel path to FitSkeletonShape
    global AdvancedSkeletonPath
    if AdvancedSkeletonPath:
        addAdvancedSkeletonPathToFitSkeleton(AdvancedSkeletonPath)

# import limbs
def importExtraLimb():
    global fitExtraLimbOptionMenu
    global limbDir
    global torsoFitJoints

    # check selection for parent joint later
    currentSelection = pm.ls(sl=1)

    if fitExtraLimbOptionMenu:
        selectedLimbFile = cmds.optionMenu(fitExtraLimbOptionMenu, q=1, v=1)
        print(selectedLimbFile)

    if not limbDir:
        raise Exception("fitSkeletonsDir is not defined")

    else:
        fitLimbFullPath = limbDir + selectedLimbFile
        print(fitLimbFullPath)

        before = set(cmds.ls(assemblies=True))

        cmds.file(fitLimbFullPath, i=1)

        after = set(cmds.ls(assemblies=True))

        imported = after.difference(before)
        limb_FitSkeleton = list(imported)[0]

        # this will mesh up selection >> use pymel
        # limb_FitSkeleton should not be changed
        autoRenamingDuplicateObjects()

        limb_FitSkeleton = pm.PyNode(limb_FitSkeleton)
        limb_FitSkeletonChildren = pm.listRelatives(limb_FitSkeleton, children=1)

        for child in limb_FitSkeletonChildren:
            if pm.nodeType(child) == 'joint':
                limb = child
            else:
                limb = None

        parentJoint = None

        if currentSelection:
            if pm.nodeType(currentSelection[0]) == 'joint':
                parentJoint = currentSelection[0]
        else:
            print('Your current selection is not joint. Trying to parent to Root')
            if torsoFitJoints:
                pm.select(torsoFitJoints[0], r=1)
                parentJoint = pm.ls(sl=1)[0]

            elif cmds.objExists("Root"):
                parentJoint = pm.PyNode("Root")

        if limb and parentJoint:
            pm.parent(limb, parentJoint)
            parentPos = pm.xform(parentJoint, q=1, t=1, ws=1)
            pm.xform(limb, t=parentPos, ws=1)
            # offset
            grandParentJoint = pm.listRelatives(parentJoint, parent=1)[0]
            # string to convert pynode to string for cmds
            offset = distanceBetweenTwoPoints(str(parentJoint), str(grandParentJoint))
            pm.xform(limb, t=(offset, 0, 0))

        else:
            pm.parent(limb, world=1)

        try:
            pm.delete(limb_FitSkeleton)
        except:
            print('no limb_FitSkeleton to be deleted')
        # # need to run update fit template here as well
        # updateFitTemplate()

def fromLabelToCode(labelName):
    codes = [0,1,2,4,18,10,12,15,16,17,18,18,18,18,18,18,18,18,18,18,18,18,18,18,18]
    labels = ["None","Root","Hip","Foot","ToesEnd","Shoulder","Hand","PropA","PropB","PropC","Other","Chest","Mid","Toes","Heel","BigToe","PinkyToe","LegAim","QToes","Eye","Wheel","0","1","2","3"]
    for label in labels:
        if label == labelName:
            indexNum = labels.index(label)
            print("code num is "+str(indexNum))
            return codes[indexNum]

def addIKLabel():
    global iKLabelOptionMenu

    currentSelection = cmds.ls(sl=1, type="joint")

    if iKLabelOptionMenu:
        selectedIKLabel = cmds.optionMenu(iKLabelOptionMenu, q=1, v=1)
        print(selectedIKLabel)

    if currentSelection:
        for joint in currentSelection:
            cmds.setAttr(joint+".drawLabel", 1)
            labelCode = fromLabelToCode(selectedIKLabel)
            cmds.setAttr(joint+".type", labelCode)
            if labelCode == 18:
                cmds.setAttr(joint+".otherType", selectedIKLabel, type="string")

def removeIKLabel():
    currentSelection = cmds.ls(sl=1, type="joint")
    for joint in currentSelection:
        cmds.setAttr(joint+".drawLabel", 0)


def addAttribute():
    global attrOptionMenu

    currentSelection = cmds.ls(sl=1)
    print(currentSelection)

    dv = 1
    meshObject = ""
    curveObject = ""

    if attrOptionMenu:
        attr = cmds.optionMenu(attrOptionMenu, q=1, v=1)

        for item in currentSelection:
            print(item)
            if cmds.attributeQuery(attr, node=item, exists=1) and cmds.objectType(item) != "joint":
                raise Exception("Attribute already added!")
            if cmds.attributeQuery(attr, node=item, exists=1) and cmds.objectType(item) == "joint":
                raise Exception("Attribute already added!")
            if attr =="twist/bendy" and cmds.attributeQuery("twistJoints", node=item, exists=1):
                raise Exception("Attribute already added!")

            if attr == "twist/bendy":
                if cmds.attributeQuery("inbetweenJoints", node=item, exists=1):
                    raise Exception("can not mix Twist and Inbetween")
                cmds.addAttr(item, ln="twistJoints", k=1, at="long", min=0, max=10, dv=2)
                cmds.addAttr(item, ln="bendyJoints", k=1, at="bool", dv=0)
            elif attr == "inbetween":
                if cmds.attributeQuery("twistJoints", node=item, exists=1):
                    raise Exception("can not mix Twist and Inbetween")
                if cmds.attributeQuery("bendyJoints", node=item, exists=1):
                    raise Exception("can not mix Twist and Inbetween")
                cmds.addAttr(item, ln="inbetweenJoints", k=1, at="long", min=0, dv=2)
                cmds.addAttr(item, ln="unTwister", k=1, at="bool", dv=0)
            elif attr == "global":
                cmds.addAttr(item, ln=attr, k=1, at="double", min=0, max=10, dv=0)
                cmds.addAttr(item, ln="globalTranslate", k=1, at="bool", dv=0)
            elif attr == "worldOrient":
                cmds.addAttr(item, ln=attr, k=1, at="enum", en="xUp:yUp:zUp:xDown:yDown:zDown:", dv=0)
            elif attr == "ikLocal":
                cmds.addAttr(item, ln=attr, k=1, at="enum", en="addCtrl:nonZero:localOrient:", dv=0)
            elif attr == "geoAttach":
                for object in currentSelection:
                    objectShape = cmds.listRelatives(object, s=1)
                    print(objectShape)
                    if objectShape and objectShape[0] != "":
                        if cmds.objectType(objectShape[0]) == "mesh":
                            meshObject = object
                            meshObject = mel.eval('substituteAllString {} ":" "__"'.format(meshObject))
                            print(meshObject)
                if len(currentSelection) < 2 or meshObject == "":
                    raise Exception("Select both FitJoint AND Geometry to attach to")
                cmds.addAttr(item, k=1, ln=attr, at="enum", en=meshObject)
                cmds.addAttr(item, k=1, ln=attr+"Mode", at="enum", en="point:orient:parent", dv=2)
                cmds.select(item)
            elif attr == "aimAt":
                for object in currentSelection:
                    print(object)
                    if cmds.objectType(object) != "joint":
                        raise Exception("Only joints must be selected")
                if currentSelection.index(item) == 1:
                    cmds.addAttr(currentSelection[1], ln=attr, k=1, at="enum", en=currentSelection[0])
                    cmds.addAttr(currentSelection[1], ln="aimAxis", k=1, at="enum", en="x:y:z", dv=0)
                    cmds.addAttr(currentSelection[1], ln="aimUpAxis", k=1, at="enum", en="x:y:z", dv=1)
                cmds.select(item)
            elif attr == "curveGuide":
                for object in currentSelection:
                    objectShape = cmds.listRelatives(object, s=1)
                    print(objectShape)
                    if objectShape and objectShape[0] != "":
                        if cmds.objectType(objectShape[0]) == "nurbsCurve":
                            curveObject = object
                            curveObject = mel.eval('substituteAllString {} ":" "__"'.format(curveObject))
                            print(curveObject)
                if len(currentSelection) < 2 or curveObject == "":
                    raise Exception("Select both FitJoint AND Curve")
                cmds.addAttr(item, k=1, ln=attr, at="enum", en=curveObject)
                cmds.addAttr(item, k=1, ln=attr+"Mode", at="enum", en="point:aim", dv=1)
                cmds.select(item)
            elif attr == "rootOptions":
                if currentSelection[0] != "Root":
                    raise Exception("Can only be added to Root joint")
                if not cmds.attributeQuery("centerBtwFeet", node=currentSelection[0], exists=1):
                    cmds.addAttr(currentSelection[0], k=1, ln="centerBtwFeet", at="bool", dv=1)
                if not cmds.attributeQuery("numMainExtras", node=currentSelection[0], exists=1):
                    cmds.addAttr(currentSelection[0], k=1, ln="numMainExtras", at="long", min=0, dv=0)
            else:
                cmds.addAttr(item, ln=attr, k=1, at="bool", dv=dv)

def removeAttribute():
    currentSelection = cmds.ls(sl=1, type='joint')
    if attrOptionMenu:
        attr = cmds.optionMenu(attrOptionMenu, q=1, v=1)

        for item in currentSelection:
            if cmds.attributeQuery(attr, node=item, exists=1):
                cmds.deleteAttr(item+"."+attr)
            if attr == "twist/bendy" and cmds.attributeQuery("twistJoints", node=item, exists=1):
                cmds.deleteAttr(item+".twistJoints")
            if attr == "twist/bendy" and cmds.attributeQuery("bendyJoints", node=item, exists=1):
                cmds.deleteAttr(item+".bendyJoints")
            if attr == "inbetween" and cmds.attributeQuery("inbetweenJoints", node=item, exists=1):
                cmds.deleteAttr(item+".inbetweenJoints")
            if attr == "inbetween" and cmds.attributeQuery("unTwister", node=item, exists=1):
                cmds.deleteAttr(item+".unTwister")
            if attr == "geoAttach" and cmds.attributeQuery("geoAttachMode", node=item, exists=1):
                cmds.deleteAttr(item+".geoAttachMode")
            if attr == "global" and cmds.attributeQuery("globalTranslate", node=item, exists=1):
                cmds.deleteAttr(item+".globalTranslate")
            if attr == "curveGuide" and cmds.attributeQuery("curveGuideMode", node=item, exists=1):
                cmds.deleteAttr(item+".curveGuideMode")
            if attr == "rootOptions" and cmds.attributeQuery("centerBtwFeet", node=item, exists=1):
                cmds.deleteAttr(item+".centerBtwFeet")
            if attr == "rootOptions" and cmds.attributeQuery("numMainExtras", node=item, exists=1):
                cmds.deleteAttr(item+".numMainExtras")
            if attr == "aimAt" and cmds.attributeQuery("aimAxis", node=item, exists=1):
                cmds.deleteAttr(item+".aimAxis")
            if attr == "aimAt" and cmds.attributeQuery("aimUpAxis", node=item, exists=1):
                cmds.deleteAttr(item+".aimUpAxis")

def getDeformJointFromFitJoint(fitJointName):
    global middleFitJoints

    # attributes >> solve it later

    deformJoints = []

    if fitJointName in middleFitJoints:
        deformJoints = [fitJointName+"_M"]
        return deformJoints

    else:
        deformJoints = [fitJointName+"_R", fitJointName+"_L"]
        return deformJoints

    return deformJoints


##############################
# start functions for meshes #
##############################

def currentSelectionPolygonal(obj):
    objType = cmds.nodeType(obj)
    if not objType == "transform":
        return False
    else:
        cmds.delete(obj, ch=1)
        # just get 1 shape node for now. Will get back later.
        shapeNode = cmds.listRelatives(obj, shapes=True)[0]
        print(shapeNode)
        nodeType = cmds.nodeType(shapeNode)
        if nodeType == "mesh":
            return True
        return False

def getDeformJoint_from_DeformJointMesh(deformJointMesh):
    deformJoint = deformJointMesh.split("_Mesh")[0]
    return deformJoint

def autoReloadPairJointsMeshesGlobal():
    global pairJointsMeshesGlobal
    pairJointsMeshesGlobal = []
    global deformJointMeshesList
    deformJointMeshesList = []

    # create structure again, just to make sure
    createStructure(None, None, None, None)

    deformJointMeshesList = cmds.listRelatives("deformJointMeshes_Grp", children=1)
    print(deformJointMeshesList)

    if deformJointMeshesList:
        for deformJointMesh in deformJointMeshesList:
            print(deformJointMesh)
            cmds.xform(deformJointMesh, cp=1)
            deformJointName = getDeformJoint_from_DeformJointMesh(deformJointMesh)
            print(deformJointName)
            pair = [deformJointName, deformJointMesh]
            print(pair)
            pairJointsMeshesGlobal.append(pair)
    print(pairJointsMeshesGlobal)
    return pairJointsMeshesGlobal

def checkIfExistingDeformJointMesh(deformJointMesh, pairJointsMeshesGlobal):
    existingDeformJointMeshes = []
    for pair in pairJointsMeshesGlobal:
        existingDeformJointMesh = pair[1]
        existingDeformJointMeshes.append(existingDeformJointMesh)
    if deformJointMesh in existingDeformJointMeshes:
        return True
    else:
        return False

def checkMeshSeparable(obj):
    # duplicate to check then delete it later
    checkMesh = cmds.duplicate(obj, name=obj + "_forCheckingSeparate")[0]

    try:
        cmds.polySeparate(checkMesh, ch=0, o=1)
        cmds.delete(checkMesh)
        return True

    except:
        cmds.delete(checkMesh)
        return False

def combineMeshesWithExisting(mesh, mergeWithExistingStatus, deformJointMeshName):
    if mesh == deformJointMeshName:
        raise Exception("current mesh is already in deformJointMeshes_Grp")
    if mergeWithExistingStatus:
        mergedMesh = cmds.polyUnite(mesh, deformJointMeshName, name=deformJointMeshName+"_merged", ch=0)[0]
        cmds.xform(mergedMesh, cp=1)
        cmds.rename(mergedMesh, deformJointMeshName)
    else:
        cmds.xform(mesh, cp=1)
        cmds.rename(mesh, deformJointMeshName)
    return deformJointMeshName

def combineThenSubmitThePairGlobal(mesh, mergeWithExistingStatus, deformJointName, deformJointMeshName):
    global pairJointsMeshesGlobal
    deformJointMesh = combineMeshesWithExisting(mesh, mergeWithExistingStatus, deformJointMeshName)
    cmds.parent(deformJointMesh, "deformJointMeshes_Grp")
    pairJointsMeshesGlobal.append([deformJointName, deformJointMesh])

def cleanUpEmptyGroups(groupName):
    if groupName and cmds.objExists(groupName):
        allGrpChildren = cmds.listRelatives(groupName, children=1, shapes=0)
        if allGrpChildren:
            deleteList = []
            for tran in allGrpChildren:
                if cmds.nodeType(tran) == 'transform':
                    children = cmds.listRelatives(tran, c=True)
                    if children==None:
                        print('%s, has no childred' % (tran))
                        deleteList.append(tran)

            if len(deleteList) > 0:
                cmds.delete(deleteList)

# separate separable side mesh
def separate_and_combine_sideMesh(obj, fitJointName):
    global pairJointsMeshesGlobal
    rightDeformJointName = fitJointName + "_R"
    rightDeformJointMesh = rightDeformJointName+"_Mesh"
    leftDeformJointName = fitJointName + "_L"
    leftDeformJointMesh = leftDeformJointName+"_Mesh"

    separableStatus = checkMeshSeparable(obj)

    if separableStatus:
        separateResults = None
        separateResults = cmds.polySeparate(obj, ch=0, o=1, name=obj+"_Piece_00")
        print(separateResults)

        rightMeshes = []
        leftMeshes = []

        for result in separateResults:
            print(result)
            cmds.xform(result, cp=1)
            xPos = cmds.xform(result, q=1, rp=1)[0]
            if xPos <= 0:
                rightMeshes.append(result)
            else:
                leftMeshes.append(result)

        if len(rightMeshes) >=1:
            mergeWithExistingStatus_Right = checkIfExistingDeformJointMesh(rightDeformJointMesh, pairJointsMeshesGlobal)

        if len(rightMeshes) > 1:
            rightMesh = cmds.polyUnite(rightMeshes, name=obj+"_R", ch=0)[0]
            print(rightMesh)

            combineThenSubmitThePairGlobal(rightMesh, mergeWithExistingStatus_Right, rightDeformJointName, rightDeformJointMesh)

        elif len(rightMeshes) == 1:
            combineThenSubmitThePairGlobal(rightMeshes[0], mergeWithExistingStatus_Right, rightDeformJointName, rightDeformJointMesh)

        else:
            rightDeformJointMesh = None


        if len(leftMeshes) >=1:
            mergeWithExistingStatus_Left = checkIfExistingDeformJointMesh(leftDeformJointMesh, pairJointsMeshesGlobal)

        if len(leftMeshes) > 1:
            leftMesh = cmds.polyUnite(leftMeshes, name=obj+"_L", ch=0)[0]
            print(leftMesh)
            combineThenSubmitThePairGlobal(leftMesh, mergeWithExistingStatus_Left, leftDeformJointName, leftDeformJointMesh)

        elif len(leftMeshes) == 1:
            combineThenSubmitThePairGlobal(leftMeshes[0], mergeWithExistingStatus_Left, leftDeformJointName, leftDeformJointMesh)

        else:
            leftDeformJointMesh = None

    else:
        cmds.xform(obj, cp=1)
        xPos = cmds.xform(obj, q=1, rp=1)[0]
        print(xPos)
        if xPos <= 0:
            print("mesh on right side of the character")
            mergeWithExistingStatus_Right = checkIfExistingDeformJointMesh(rightDeformJointMesh, pairJointsMeshesGlobal)
            combineThenSubmitThePairGlobal(obj, mergeWithExistingStatus_Right, rightDeformJointName, rightDeformJointMesh)

        else:
            print("mesh on left side of the character")
            mergeWithExistingStatus_Left = checkIfExistingDeformJointMesh(leftDeformJointMesh, pairJointsMeshesGlobal)
            combineThenSubmitThePairGlobal(obj, mergeWithExistingStatus_Left, leftDeformJointName, leftDeformJointMesh)

    cleanUpEmptyGroups("dupMeshesForCut_Grp")
    cleanUpEmptyGroups("faceItems_Grp")
    cmds.select(clear=1)


def addMiddleJointMesh(mesh, fitJointName):
    global pairJointsMeshesGlobal
    global meshSmoothStatus

    middleDeformJointName = getDeformJointFromFitJoint(fitJointName)[0]
    print(middleDeformJointName)
    middleDeformJointMesh = middleDeformJointName+"_Mesh"
    print(middleDeformJointMesh)
    if mesh == middleDeformJointMesh:
        if cmds.objExists("temp_mesh"):
            cmds.rename("temp_mesh", "renamedMesh_toAvoidConflict")
        cmds.rename(mesh, "temp_mesh")
        mesh = "temp_mesh"

    mergeWithExisting = checkIfExistingDeformJointMesh(middleDeformJointMesh, pairJointsMeshesGlobal)
    print(mergeWithExisting)
    middleDeformJointMesh = combineMeshesWithExisting(mesh, mergeWithExisting, middleDeformJointMesh)
    print(middleDeformJointMesh)

    # center pivot
    cmds.xform(middleDeformJointMesh, cp=1, ws=1)

    # not sure why "deformJointMeshes_Grp" disappeared. How?
    createStructure(None, None, None, None)
    cmds.parent(middleDeformJointMesh, "deformJointMeshes_Grp")

    pairJointsMeshesGlobal.append([middleDeformJointName, middleDeformJointMesh])
    print(pairJointsMeshesGlobal)
    cmds.select(clear=1)
    cleanUpEmptyGroups("dupMeshesForCut_Grp")
    cleanUpEmptyGroups("faceItems_Grp")
    return pairJointsMeshesGlobal

def changeAddBtnColor(fitJointName, color=[0.3, 0, 0]):
    global torsoFitJoints
    global torsoCutButtons
    global torsoAddButtons

    if torsoFitJoints and torsoCutButtons and torsoAddButtons and fitJointName in torsoFitJoints:
        jntIndex = torsoFitJoints.index(fitJointName)
        cmds.button(torsoCutButtons[jntIndex], e=True, bgc=color)
        cmds.button(torsoAddButtons[jntIndex], e=True, bgc=color)

    global armFitJointsGlobal
    global armCutButtonsGlobal
    global armAddButtonsGlobal
    if all(armFitJointsGlobal) and all(armCutButtonsGlobal) and all(armAddButtonsGlobal):
        for armFitJoints in armFitJointsGlobal:
            listIndex = armFitJointsGlobal.index(armFitJoints)
            if fitJointName in armFitJoints:
                jntIndex = armFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(armCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(armAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

    global fingersFitJointsGlobal
    global fingersCutButtonsGlobal
    global fingersAddButtonsGlobal
    if all(fingersFitJointsGlobal) and all(fingersCutButtonsGlobal) and all(fingersAddButtonsGlobal):
        for fingersFitJoints in fingersFitJointsGlobal:
            listIndex = fingersFitJointsGlobal.index(fingersFitJoints)
            if fitJointName in fingersFitJoints:
                jntIndex = fingersFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(fingersCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(fingersAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

    global legFitJointsGlobal
    global legCutButtonsGlobal
    global legAddButtonsGlobal
    if all(legFitJointsGlobal) and all(legCutButtonsGlobal) and all(legAddButtonsGlobal):
        for legFitJoints in legFitJointsGlobal:
            listIndex = legFitJointsGlobal.index(legFitJoints)
            if fitJointName in legFitJoints:
                jntIndex = legFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(legCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(legAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

    global toesIndividualFitJointsGlobal
    global toesCutButtonsGlobal
    global toesAddButtonsGlobal
    if all(toesIndividualFitJointsGlobal) and all(toesCutButtonsGlobal) and all(toesAddButtonsGlobal):
        for toesIndividualFitJoints in toesIndividualFitJointsGlobal:
            listIndex = toesIndividualFitJointsGlobal.index(toesIndividualFitJoints)
            if fitJointName in toesIndividualFitJoints:
                jntIndex = toesIndividualFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(toesCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(toesAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

    global iKSplineFitJointsGlobal
    global ikSplinesCutButtonsGlobal
    global ikSplinesAddButtonsGlobal
    if all(iKSplineFitJointsGlobal) and all(ikSplinesCutButtonsGlobal) and all(ikSplinesAddButtonsGlobal):
        for iKSplineFitJoints in iKSplineFitJointsGlobal:
            listIndex = iKSplineFitJointsGlobal.index(iKSplineFitJoints)
            if fitJointName in iKSplineFitJoints:
                jntIndex = iKSplineFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(ikSplinesCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(ikSplinesAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

    global fKFitJointsGlobal
    global fkCutButtonsGlobal
    global fkAddButtonsGlobal
    if all(fKFitJointsGlobal) and all(fkCutButtonsGlobal) and all(fkAddButtonsGlobal):
        for fKFitJoints in fKFitJointsGlobal:
            listIndex = fKFitJointsGlobal.index(fKFitJoints)
            if fitJointName in fKFitJoints:
                jntIndex = fKFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(fkCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(fkAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

    global faceItemsFitJointsGlobal
    global faceCutButtonsGlobal
    global faceAddButtonsGlobal
    if all(faceItemsFitJointsGlobal) and all(faceCutButtonsGlobal) and all(faceAddButtonsGlobal):
        for faceItemsFitJoints in faceItemsFitJointsGlobal:
            listIndex = faceItemsFitJointsGlobal.index(faceItemsFitJoints)
            if fitJointName in faceItemsFitJoints:
                jntIndex = faceItemsFitJoints.index(fitJointName)

                # use list index and joint index to have button index
                cmds.button(faceCutButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)
                cmds.button(faceAddButtonsGlobal[listIndex][jntIndex], e=True, bgc=color)

def changeClearBtnColor(fitJointName, color=[0, 0.4, 0]):
    global torsoFitJoints
    global torsoClearButtons

    if torsoFitJoints and torsoClearButtons and fitJointName in torsoFitJoints:
        jntIndex = torsoFitJoints.index(fitJointName)
        cmds.button(torsoCutButtons[jntIndex], e=True, bgc=color)
        cmds.button(torsoAddButtons[jntIndex], e=True, bgc=color)

# this one is for adding already cut deform joint mesh into pairJointsMeshesGlobal
def findSideThenAddDeformJointMesh(fitJointName):
    global middleFitJoints
    global pairJointsMeshesGlobal

    objectList = cmds.ls(sl=1, flatten=1)
    print(objectList)

    if not currentSelectionPolygonal(objectList[0]):
        raise Exception("Please select polygonal objects")

    meshSmoothStatus = 0
    # double check smooth mesh preview
    for object in objectList:
        currentMeshSmoothStatus = cmds.getAttr(object + '.displaySmoothMesh')
        if currentMeshSmoothStatus:
            meshSmoothStatus = currentMeshSmoothStatus

    print(meshSmoothStatus)
    if meshSmoothStatus != 0:
        # no smooth at all
        for obj in objectList:
            cmds.setAttr(obj + '.displaySmoothMesh', 0)

    # need to run auto load pairJointeMeshesGlobal
    autoReloadPairJointsMeshesGlobal()
    print(pairJointsMeshesGlobal)

    if len(objectList) > 1:
        if fitJointName in middleFitJoints:
            for obj in objectList:
                print(obj)
                if not currentSelectionPolygonal(obj):
                    raise Exception("Please select polygonal objects")

            middleMesh = cmds.polyUnite(objectList, ch=0, name="merged_middle_mesh")
            print(middleMesh)

            addMiddleJointMesh(middleMesh, fitJointName)
            changeAddBtnColor(fitJointName)

        else:
            # cannot loop with rename, so we will combine first, then separate later
            for obj in objectList:
                print(obj)
                if not currentSelectionPolygonal(obj):
                    raise Exception("Please select polygonal objects")

            mergedObj = cmds.polyUnite(objectList, name="temp_merged_to_separate", ch=0)[0]
            separate_and_combine_sideMesh(mergedObj, fitJointName)
            print(pairJointsMeshesGlobal)
            if cmds.objExists(mergedObj):
                cmds.delete(mergedObj)
            changeAddBtnColor(fitJointName)
            return pairJointsMeshesGlobal

    elif len(objectList) == 1:
        if fitJointName in middleFitJoints:
            print("working with middle fit joint")
            if not currentSelectionPolygonal(objectList[0]):
                raise Exception("Please select polygonal objects")

            addMiddleJointMesh(objectList[0], fitJointName)
            changeAddBtnColor(fitJointName)

        else:
            separate_and_combine_sideMesh(objectList[0], fitJointName)
            print(pairJointsMeshesGlobal)
            changeAddBtnColor(fitJointName)

    else:
        raise Exception("Please select polygonal mesh(es)")



def getFaceListOnNewMesh(faceList, newMesh):
    newMeshFaceList=[]
    for face in faceList:
        newMeshFace = newMesh + "." + face.split('.')[1]
        newMeshFaceList.append(newMeshFace)

    print(newMeshFaceList)
    return newMeshFaceList

def deleteToggleFaces(keptFaceList, currentMesh):
    cmds.select(keptFaceList, r=True)
    # toggle not-selected faces, then delete them
    cmds.select(currentMesh+".f[*]", tgl=True)
    cmds.delete()

# check type of selection (faces, vertices or edges)
# need to show error when something else was selected
selectiontype = namedtuple('selectiontype', 'faces verts edges')
def get_selected_components():
    sel = cmds.ls(sl=True, type='float3')
    faces = cmds.polyListComponentConversion(sel, ff=True, tf =True)
    verts = cmds.polyListComponentConversion(sel, fv=True, tv =True)
    edges = cmds.polyListComponentConversion(sel, fe=True, te =True)
    return selectiontype(faces, verts, edges)

# just get name of the first face, first mesh. Should be one mesh only.
def getObjectNameFromFaceName(faceList):
    objectName = faceList[0].split('.')[0]
    return objectName

def findSideThenCutFaces_toCreate_DeformJointMesh(fitJointName):
    global middleFitJoints
    global pairJointsMeshesGlobal
    # get face selection
    currentFaceSelectionList = cmds.ls(sl=1, flatten=1)

    # need to check node type of current selection. Different than faces then raise error
    selected = get_selected_components()
    if not selected.faces:
        raise Exception("Please select some faces")

    # get object name from face name
    objectName = getObjectNameFromFaceName(currentFaceSelectionList)

    # double check smooth mesh preview
    meshSmoothStatus = cmds.getAttr(objectName + '.displaySmoothMesh')
    if meshSmoothStatus != 0:
        # no smooth at all
        cmds.setAttr(objectName + '.displaySmoothMesh', 0)

    # clean up empty groups
    cleanUpEmptyGroups("dupMeshesForCut_Grp")
    cleanUpEmptyGroups("deformJointMeshes_Grp")

    # create new "cutMesh"
    jointMesh = cmds.duplicate(objectName, name=objectName+"_dup_for_being_deformJntMesh_later")[0]

    # get new face list from old face list, toggle & delete
    jointMeshFaceList = getFaceListOnNewMesh(currentFaceSelectionList, jointMesh)

    # delete face selection from current mesh
    cmds.delete(currentFaceSelectionList)
    # use the "cutMesh" for object functions
    deleteToggleFaces(jointMeshFaceList, jointMesh)

    # center pivot jointMesh for easy calculation later
    cmds.xform(jointMesh, cp=1, ws=1)

    cmds.select(jointMesh, replace=1)
    findSideThenAddDeformJointMesh(fitJointName)

    # get back the smoothness
    cmds.setAttr(objectName + '.displaySmoothMesh', meshSmoothStatus)



####################################################
# functions to clear deform joint meshes variables #
####################################################

# a function to clear current pair from pairJointsMeshesGlobal
# This is clear from the list, unhide, unparent from deformJointMeshes_Grp
# Also, change the mesh name (to avoid conflict)
def clearPairFromPairJointsMeshesGlobal(fitJointName, color=[0, 0, 0]):
    global pairJointsMeshesGlobal

    cmds.showHidden("dupMeshesForCut_Grp")

    autoReloadPairJointsMeshesGlobal()
    deformJointsList = getDeformJointFromFitJoint(fitJointName)
    print(deformJointsList)

    needToBeClearedPair = []
    # deform joint mesh names >> for checking the whole scene
    deformJointMeshList = []

    for deformJoint in deformJointsList:
        deformJointMesh = deformJoint+"_Mesh"

        if cmds.objExists(deformJointMesh):
            cmds.parent(deformJointMesh, "dupMeshesForCut_Grp")
            pair = [deformJoint, deformJointMesh]
            print(pair)
            needToBeClearedPair.append(pair)
            deformJointMeshList.append(deformJointMesh)

    if needToBeClearedPair:
        print(needToBeClearedPair)
        for pair in needToBeClearedPair:
            try:
                pairJointsMeshesGlobal.remove(pair)
            except:
                print("This pair is not in pair Global list")

        # double check pair global
        print(pairJointsMeshesGlobal)

    # rename using pymel
    pm.select(deformJointMeshList, replace=1)
    pyDeformJointMeshNames = pm.ls(sl=1)
    print(pyDeformJointMeshNames)
    for mesh in pyDeformJointMeshNames:
        # just in case this deform joint mesh is outside the system
        try:
            cmds.parent(mesh, "dupMeshesForCut_Grp")
        except:
            print("This mesh is already under dupMeshesForCut_Grp")
        # always center pivot, just to make sure
        pm.xform(mesh, cp=1)
        pm.rename(mesh, "mesh_to_be_cut_again")

    changeClearBtnColor(fitJointName)

#################################
# functions for joint placement #
#################################

def detectPreviousDeformJointMesh(fitJointName):
    # check if there is Fit Skeleton
    if not cmds.objExists("FitSkeleton"):
        raise Exception("Fit Skeleton need to be imported first")
    # need to change this to the top joint (under Fit Skeleton)
    elif fitJointName == "Root":
        return None
    else:
        allFitJointParents = cmds.ls(fitJointName, long=True)[0].split('|')[1:-1]
        allFitJointParents.reverse()
        print(allFitJointParents)

        # if previous joint has no deform joint mesh, continue look for previous joints until found one
        for parentFitJoint in allFitJointParents:
            print(parentFitJoint)
            deformJointName = getDeformJointFromFitJoint(parentFitJoint)[0]
            print(deformJointName)
            previousDeformJointMesh = deformJointName + "_Mesh"
            print(previousDeformJointMesh)
            if cmds.objExists(previousDeformJointMesh):
                print(previousDeformJointMesh)
                return previousDeformJointMesh
            if parentFitJoint == "FitSkeleton":
                print("cannot find previous deformJointMesh")
                return None
        print("cannot find previous deformJointMesh_")
        return None

def getFitJointNameFromDeformJointName(deformJointName):
    fitJointName = deformJointName[:-2]
    if "Part" in fitJointName:
        fitJointName = fitJointName.split("Part")[0]
    side = deformJointName[-2:]
    fitJoint_and_Side_list = [fitJointName, side]
    return fitJoint_and_Side_list

# if non vertice is intersecting, then use closet ver.
# Need to find the mesh center though >> use average pivot of 2 objects
def getClosestVert(deformJointMesh, previousDeformJointMesh):
    geo = pm.PyNode(previousDeformJointMesh) # user input (from UI) needed!
    fPG = pm.PyNode(deformJointMesh) # convert to PyNode
    pos = fPG.getRotatePivot(space='world')

    nodeDagPath = OpenMaya.MObject()
    try:
        selectionList = OpenMaya.MSelectionList()
        selectionList.add(geo.name())
        nodeDagPath = OpenMaya.MDagPath()
        selectionList.getDagPath(0, nodeDagPath)
    except:
        raise RuntimeError('OpenMaya.MDagPath() failed on %s' % geo.name())

    mfnMesh = OpenMaya.MFnMesh(nodeDagPath)

    pointA = OpenMaya.MPoint(pos.x, pos.y, pos.z)
    pointB = OpenMaya.MPoint()
    space = OpenMaya.MSpace.kWorld

    util = OpenMaya.MScriptUtil()
    util.createFromInt(0)
    idPointer = util.asIntPtr()

    mfnMesh.getClosestPoint(pointA, pointB, space, idPointer)
    idx = OpenMaya.MScriptUtil(idPointer).asInt()

    faceVerts = [geo.vtx[i] for i in geo.f[idx].getVertices()]
    closestVert = None
    minLength = None
    for v in faceVerts:
        thisLength = (pos - v.getPosition(space='world')).length()
        if minLength is None or thisLength < minLength:
            minLength = thisLength
            closestVert = v
    return str(closestVert)

def getCenterOfVertices(vertices):
    n = len(vertices)
    centerX = 0
    centerY = 0
    centerZ = 0
    for ver in vertices:
        pos = cmds.xform(ver, q=True, translation=True, ws=True)
        print(pos)
        centerX = centerX + pos[0]
        centerY = centerY + pos[1]
        centerZ = centerZ + pos[2]
    centerPos = [centerX/n, centerY/n, centerZ/n]
    return centerPos

def getVertPositions(objectList, objectNumber):
    count = 0
    pointList = []

    iter = OpenMaya.MItSelectionList(objectList, OpenMaya.MFn.kGeometric)
    while not iter.isDone():
        count = count + 1
        if (count != objectNumber):
            iter.next()

        dagPath = OpenMaya.MDagPath()
        iter.getDagPath(dagPath)
        mesh = OpenMaya.MFnMesh(dagPath)

        meshPoints = OpenMaya.MPointArray()
        mesh.getPoints(meshPoints, OpenMaya.MSpace.kWorld)

        for point in range(meshPoints.length()):
            pointList.append([meshPoints[point][0], meshPoints[point][1], meshPoints[point][2]])
        return pointList

def hashPoints(pointList):
    _clamp = lambda p: hash(int(p * 10000) / 10000.00)

    hashedPointList = []

    for point in pointList:
        hashedPointList.append(hash(tuple(map(_clamp, point))))

    return (hashedPointList)

def getPairIndices(hashListOne, hashListTwo, matchingHashList):
    pairedVertIndices = []
    vertOneIndexList = []
    vertTwoIndexList = []

    for hash in matchingHashList:
        vertListOne = []
        vertListTwo = []

        for hashOne in range(len(hashListOne)):
            if (hashListOne[hashOne] == hash):
                vertListOne.append(hashOne)

        for hashTwo in range(len(hashListTwo)):
            if (hashListTwo[hashTwo] == hash):
                vertListTwo.append(hashTwo)

        pairedVertIndices.append([vertListOne, vertListTwo])

    return pairedVertIndices

def getIntersectingVertices(currentDeformJointMesh, previousDeformJointMesh):
    cmds.select(currentDeformJointMesh, previousDeformJointMesh, r=1)
    selectionList = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selectionList)

    meshOneVerts = getVertPositions(selectionList, 1)
    meshTwoVerts = getVertPositions(selectionList, 2)

    meshOneHashedPoints = hashPoints(meshOneVerts)
    meshTwoHashedPoints = hashPoints(meshTwoVerts)

    matchingVertList = set(meshOneHashedPoints).intersection(meshTwoHashedPoints)

    pairedVertList = getPairIndices(meshOneHashedPoints, meshTwoHashedPoints, matchingVertList)

    cmds.select(clear=1)
    for pair in pairedVertList:
        cmds.select("{0}.vtx[{1}]".format(currentDeformJointMesh, pair[0][0]), add=1)
    intersectingVertices = cmds.ls(sl=1, flatten=1)
    return intersectingVertices

def getCenterOfVerticesBasedOnManip(vertices):
    cmds.select(vertices, replace=1)
    cmds.setToolTo("Move")
    centerPos = cmds.manipMoveContext("Move", q=1, p=1)
    print(centerPos)
    return centerPos

def findMiddlePointPos(p1, p2):
    midPointPos = [(p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2]
    return midPointPos

def mergeVertices_deformJointMeshes():
    global deformJointMeshesList
    if not deformJointMeshesList:
        autoReloadPairJointsMeshesGlobal()
    for deformJointMesh in deformJointMeshesList:
        cmds.polyMergeVertex(deformJointMesh, distance=0.001, ch=0)

def getFitJointPosition(fitJointName, currentDeformJointMesh, previousDeformJointMesh):
    global middleFitJoints

    if fitJointName.startswith("Eye"):
        centerPos = cmds.xform(currentDeformJointMesh, q=1, rp=1, ws=1)
        return centerPos
    else:
        # if no previous deform joint mesh >> snap to previous fit joint
        parentFitJoint = cmds.listRelatives(fitJointName, parent=1)
        parentPos = cmds.xform(parentFitJoint, q=1, t=1, ws=1)
        # if previous deformJointMesh and current deform joint mesh are intersecting
        if currentDeformJointMesh and previousDeformJointMesh:
            intersectingVertices = getIntersectingVertices(currentDeformJointMesh, previousDeformJointMesh)
            if intersectingVertices:
                centerPos = getCenterOfVerticesBasedOnManip(intersectingVertices)
                if fitJointName in middleFitJoints:
                    centerPos = [0, centerPos[1], centerPos[2]]
                print(centerPos)
                # # testing position
                # cmds.spaceLocator(p=centerPos)
                return centerPos
            else:
                print("No intersecting, finding the closest vertex")
                closestVertexOnPreviousMesh = getClosestVert(currentDeformJointMesh, previousDeformJointMesh)
                closestVertexOnPreviousMeshPos = cmds.xform(closestVertexOnPreviousMesh, q=1, t=1, ws=1)
                closestVertexOnCurrentMesh = getClosestVert(previousDeformJointMesh, currentDeformJointMesh)
                closestVertexOnCurrentMeshPos = cmds.xform(closestVertexOnCurrentMesh, q=1, t=1, ws=1)

                currentDeformJointMeshPivotPos = cmds.xform(currentDeformJointMesh, q=1, rp=1)
                previousDeformJointMeshPivotPos = cmds.xform(previousDeformJointMesh, q=1, rp=1)

                # use middle pos between pivot and closest point in 2 meshes to find final middle pos
                # will find better solution later.
                middlePosOnCurrentMesh = findMiddlePointPos(closestVertexOnCurrentMeshPos, currentDeformJointMeshPivotPos)
                middlePosOnPreviousMesh = findMiddlePointPos(closestVertexOnPreviousMeshPos, previousDeformJointMeshPivotPos)

                centerPos = findMiddlePointPos(middlePosOnCurrentMesh, middlePosOnPreviousMesh)

                if fitJointName in middleFitJoints:
                    centerPos = [0, centerPos[1], centerPos[2]]
                print(centerPos)
                # testing position
                # cmds.spaceLocator(p=centerPos)
                return centerPos

        else:
            return parentPos

#######################
# Building Everything #
#######################
def sortPairJointsMeshesGlobal():
    global pairJointsMeshesGlobal
    newPairJointsMeshesGlobal = []
    # this is for sorting torso joints
    for pair in pairJointsMeshesGlobal:
        print(pair)
        # check deform joint mesh exists or not
        if cmds.objExists(pair[1]):
            fitJointName = getFitJointNameFromDeformJointName(pair[0])[0]
            print(fitJointName)
            # check if fitJointName exists or not
            if cmds.objExists(fitJointName):
                path = cmds.ls(fitJointName, long=1)[0]
                print(path)
                pathSplit = path.split("|")
                pathLength = len(pathSplit)
                print(pathLength)
                pair.append(pathLength)
                print(pair)
                newPairJointsMeshesGlobal.append(pair)

    print(newPairJointsMeshesGlobal)
    newPairJointsMeshesGlobal.sort(key=lambda i: i[2])
    print(newPairJointsMeshesGlobal)

    pairJointsMeshesGlobal = []

    for list in newPairJointsMeshesGlobal:
        list.remove(list[-1])
        pairJointsMeshesGlobal.append(list)
    print(pairJointsMeshesGlobal)
    return pairJointsMeshesGlobal

# make sure knee and elbow dont flip
def placeKneeJoints():
    # look for knee & elbow joints >> offset them to avoid flipping
    global footFitJointsGlobal
    global torsoFitJoints
    if footFitJointsGlobal:
        for footFitJoint in footFitJointsGlobal:
            print(footFitJoint)
            footZ = cmds.xform(footFitJoint, q=1, t=1, ws=1)[2]
            kneeJoint = cmds.listRelatives(footFitJoint, parent=1)[0]
            hipJoint = cmds.listRelatives(kneeJoint, parent=1)[0]
            hipZ = cmds.xform(hipJoint, q=1, t=1, ws=1)[2]
            print(hipZ)
            maxZ = None
            if hipZ >= footZ:
                maxZ=hipZ
            else:
                maxZ=footZ
            print(maxZ)
            kneePos = cmds.xform(kneeJoint, q=1, t=1, ws=1)
            print(kneePos)

            if kneePos[2] < maxZ:
                kneeChildren = cmds.listRelatives(kneeJoint, children=1)
                cmds.parent(kneeChildren, torsoFitJoints[0])
                cmds.parent(kneeJoint, torsoFitJoints[0])
                cmds.xform(kneeJoint, t=[kneePos[0], kneePos[1], maxZ], ws=1)
                cmds.parent(kneeChildren, kneeJoint)
                cmds.parent(kneeJoint, hipJoint)

def placeElbowJoints():
    global handFitJointsGlobal
    global torsoFitJoints
    if handFitJointsGlobal:
        for handFitJoint in handFitJointsGlobal:
            print(handFitJoint)
            handZ = cmds.xform(handFitJoint, q=1, t=1, ws=1)[2]
            elbowJoint = cmds.listRelatives(handFitJoint, parent=1)[0]
            shoulderJoint = cmds.listRelatives(elbowJoint, parent=1)[0]
            shoulderZ = cmds.xform(shoulderJoint, q=1, t=1, ws=1)[2]
            minZ = None
            if shoulderZ <= handZ:
                minZ = shoulderZ
            else:
                minZ = handZ
            print(minZ)
            elbowPos = cmds.xform(elbowJoint, q=1, t=1, ws=1)
            print(elbowPos)

            if elbowPos[2] > minZ:
                elbowChildren = cmds.listRelatives(elbowJoint, children=1)
                cmds.parent(elbowChildren, torsoFitJoints[0])
                cmds.parent(elbowJoint, torsoFitJoints[0])
                cmds.xform(elbowJoint, t=[elbowPos[0], elbowPos[1], minZ], ws=1)
                cmds.parent(elbowChildren, elbowJoint)
                cmds.parent(elbowJoint, shoulderJoint)

def distanceBetweenTwoPoints(objA, objB):
    gObjA = cmds.xform(objA, q=True, t=True, ws=True)
    gObjB = cmds.xform(objB, q=True, t=True, ws=True)
    return sqrt(pow(gObjA[0] - gObjB[0], 2) + pow(gObjA[1] - gObjB[1], 2) + pow(gObjA[2] - gObjB[2], 2))

def distanceBetweenTwoPointsRP(objA, objB):
    gObjA = cmds.xform(objA, q=True, rp=True, ws=True)
    gObjB = cmds.xform(objB, q=True, rp=True, ws=True)
    return sqrt(pow(gObjA[0] - gObjB[0], 2) + pow(gObjA[1] - gObjB[1], 2) + pow(gObjA[2] - gObjB[2], 2))

def distanceBetweenTwoPositions(gObjA, gObjB):
    return sqrt(pow(gObjA[0] - gObjB[0], 2) + pow(gObjA[1] - gObjB[1], 2) + pow(gObjA[2] - gObjB[2], 2))

def findFaceItemsEndJoints():
    global faceItemsFitJointsGlobal
    global iKSplineFitJointsGlobal

    faceItemsEndJoints = []

    if faceItemsFitJointsGlobal:
        for faceItemsFitJoints in faceItemsFitJointsGlobal:
            # list all children of head joint
            allChildrenJoints = cmds.listRelatives(faceItemsFitJoints[0], children=1, ad=1)
            for joint in allChildrenJoints:
                print(joint)
                # skip ikSpline joints
                drawLabelStatus = cmds.getAttr(joint + ".drawLabel")
                jointLabel = cmds.getAttr(joint + ".otherType")
                numList = [int(s) for s in jointLabel.split() if s.isdigit()]
                # skip iKSpline joints in Face End joints
                if drawLabelStatus and numList:
                    print("Passing "+joint)
                    pass
                else:
                    if not cmds.listRelatives(joint, children=1):
                        # this one is the correct end joint
                        faceItemsEndJoints.append(joint)
                        print("added "+joint+" into faceItemsEndJoints")

        print(faceItemsEndJoints)
        return faceItemsEndJoints

def findClosestVerOnMesh_to_Point(point, Mesh):
    # find the closest vertex on main mesh to current vertex (on prop)
    pos = []
    pos = cmds.xform(point, q=1, ws=1, t=1)
    cpom = cmds.createNode('closestPointOnMesh')
    shape = cmds.listRelatives(Mesh, s=True)[0]
    cmds.connectAttr('%s.outMesh' % shape, '%s.inMesh' % cpom)
    cmds.setAttr('%s.inPosition' % cpom, pos[0], pos[1], pos[2], type="double3")

    # vertex index
    vtxIndx = cmds.getAttr(cpom + ".closestVertexIndex")
    closestVer = "{0}.vtx[{1}]".format(Mesh, vtxIndx)

    # delete node when done calculating
    cmds.delete(cpom)

    return closestVer


def placingEndJointProcess(endJoint, axis):
    # distance 01:
    distance1 = None
    distance2 = None

    # find parent joint of the current end joint
    endJointParent = cmds.listRelatives(endJoint, parent=1)[0]
    print(endJointParent)
    # find grand-parent joint of the current end joint
    endJointGrandParent = cmds.listRelatives(endJointParent, parent=1)[0]
    print(endJointGrandParent)
    # return the distance between parent joint and grand-parent joint (distance 01)
    distance1 = distanceBetweenTwoPoints(endJointParent, endJointGrandParent)
    print(distance1)
    # look for deform joint mesh of parent joint.
    endJointParentDeformJointMesh = getDeformJointFromFitJoint(endJointParent)[0] + "_Mesh"
    print(endJointParentDeformJointMesh)
    if not cmds.objExists(endJointParentDeformJointMesh):
        # if obj doesn't exist > return None for distance 02
        distance2 = None
        print(distance2)
    else:
        # else: mesh --> BBox, find maxX, maxY, maxZ >> max of all = distance 02
        bBoxSize = cmds.exactWorldBoundingBox(endJointParentDeformJointMesh)
        Xsize = bBoxSize[3]-bBoxSize[0]
        Ysize = bBoxSize[4]-bBoxSize[1]
        Zsize = bBoxSize[5]-bBoxSize[2]
        distance2 = max([Xsize, Ysize, Zsize])
        print(distance2)

    maxDistance = None
    # distance 01 vs 02. Bigger = final distance
    if distance1 >= distance2:
        maxDistance = distance1
        print("using distance1 (previous distance)")
    else:
        maxDistance = distance2
        print("using distance2 (max BBox)")
    print(maxDistance)

    # set current end joint pos = [0,0,0]
    endJointParentPos = cmds.xform(endJointParent, q=1, t=1, ws=1)
    cmds.xform(endJoint, t=endJointParentPos, ws=1)
    print("snapped endJoint to endJointParent")

    # turn on fit mode to update orientation
    mel.eval('asFitModeManualUpdate')

    if axis == "X":
        # move X out with final distance
        # ws worked? Or relative space?? How? >> Ear issue??
        cmds.xform(endJoint, t=[maxDistance, 0, 0])
        print("moved maxDistance")

        # look for closest vertex on deform joint mesh. If deform joint mesh doesn't exist. Pass
        if endJointParentDeformJointMesh and cmds.objExists(endJointParentDeformJointMesh):
            ver = findClosestVerOnMesh_to_Point(endJoint, endJointParentDeformJointMesh)
            # to avoid crash Maya
            cmds.select(ver, replace=1)
            closestVer = cmds.ls(sl=1)[0]
            # find distance from parent joint to this closest vertex >> finalX distance. Move end joint.
            finalX = distanceBetweenTwoPoints(closestVer, endJointParent)
            cmds.xform(endJoint, t=[finalX, 0, 0])
        else:
            pass

    elif axis == "Y":
        # move Y out with final distance
        cmds.xform(endJoint, t=[0, maxDistance, 0])
        print("moved maxDistance")

        # look for closest vertex on deform joint mesh. If deform joint mesh doesn't exist. Pass
        if endJointParentDeformJointMesh and cmds.objExists(endJointParentDeformJointMesh):
            ver = findClosestVerOnMesh_to_Point(endJoint, endJointParentDeformJointMesh)
            cmds.select(ver, replace=1)
            closestVer = cmds.ls(sl=1)[0]
            finalY = distanceBetweenTwoPoints(closestVer, endJointParent)
            cmds.xform(endJoint, t=[0, finalY, 0])
        else:
            pass


def placeEndJoint_basedOn_BBoxPreviousMesh(endJoint, axis):
    global torsoFitJoints
    # find parent joint of the current end joint
    endJointParent = cmds.listRelatives(endJoint, parent=1)[0]
    print(endJointParent)
    endJointParentDeformJointMesh = getDeformJointFromFitJoint(endJointParent)[0] + "_Mesh"
    print(endJointParentDeformJointMesh)

    currentPos = cmds.xform(endJoint, q=1, t=1, ws=1)

    if not cmds.objExists(endJointParentDeformJointMesh):
        cmds.xform(endJoint, t=[currentPos[0], 0, currentPos[2]])
    else:
        if torsoFitJoints:
            bBoxSize = cmds.exactWorldBoundingBox(endJointParentDeformJointMesh)
            # Heel
            if axis == "-Z":
                cmds.xform(endJoint, t=(currentPos[0], 0, bBoxSize[2]), ws=1)

            # PinkyToe
            elif axis == "-X":
                cmds.xform(endJoint, t=(bBoxSize[0], 0, currentPos[2]), ws=1)

            # BigToe
            elif axis == "+X":
                cmds.xform(endJoint, t=(bBoxSize[3], 0, currentPos[2]), ws=1)

# using fitmode to offset X, to reach bbox of the mesh
# if toeEnd >> Y (ws) = 0
# pinkyToe >> right side, Y(ws) = 0. If not bbox, just Y
# bigToe >> left side, Y(ws) = 0. If not bbox, just Y
# heel >> back, Y(ws) = 0. If not bbox, just Y
def placeEndJointIntoPlace():
    global endJointsList
    global toesEndFitJointsGlobal
    global pinkyToeFitJointsGlobal
    global bigToeFitJointsGlobal
    global heelFitJointsGlobal

    finalEndJointList = []
    # no need to place face end joints. Solve pinky, bigToes and heel later.
    if endJointsList:
        finalEndJointList = endJointsList
        faceItemEndJoints = findFaceItemsEndJoints()
        print(faceItemEndJoints)
        if faceItemEndJoints:
            finalEndJointList = filterOutListOfJoints(endJointsList, faceItemEndJoints)

        if pinkyToeFitJointsGlobal:
            finalEndJointList = filterOutListOfJoints(finalEndJointList, pinkyToeFitJointsGlobal)

        if bigToeFitJointsGlobal:
            finalEndJointList = filterOutListOfJoints(finalEndJointList, bigToeFitJointsGlobal)

        if heelFitJointsGlobal:
            finalEndJointList = filterOutListOfJoints(finalEndJointList, heelFitJointsGlobal)

        if toesEndFitJointsGlobal:
            finalEndJointList = filterOutListOfJoints(finalEndJointList, toesEndFitJointsGlobal)

        print(finalEndJointList)
        for endJoint in finalEndJointList:
            print(endJoint)
            placingEndJointProcess(endJoint, "X")
            cmds.refresh()


    # toeEnds. Same process but with Y axis
    if toesEndFitJointsGlobal:
        for toesEndFitJoint in toesEndFitJointsGlobal:
            print(toesEndFitJoint)
            placingEndJointProcess(toesEndFitJoint, "Y")
            # adjust Y(ws)
            pos = cmds.xform(toesEndFitJoint, q=1, t=1, ws=1)
            cmds.xform(toesEndFitJoint, t=[pos[0], 0, pos[2]], ws=1)
            cmds.refresh()

    # heels
    if heelFitJointsGlobal:
        for endJoint in heelFitJointsGlobal:
            print(endJoint)
            placeEndJoint_basedOn_BBoxPreviousMesh(endJoint, "-Z")
            cmds.refresh()

    # pinkyToes
    if pinkyToeFitJointsGlobal:
        for endJoint in pinkyToeFitJointsGlobal:
            print(endJoint)
            placeEndJoint_basedOn_BBoxPreviousMesh(endJoint, "-X")
            cmds.refresh()

    # bigToes
    if bigToeFitJointsGlobal:
        for endJoint in bigToeFitJointsGlobal:
            print(endJoint)
            placeEndJoint_basedOn_BBoxPreviousMesh(endJoint, "+X")
            cmds.refresh()

# some joints are not in "Snap-to-projected center". How to fix?
# need to sort joints from parent to child >> place parent first, child later. End joints last.
# if the previous joint has not deformJointMesh >> look for previous joint until it see a deform mesh
# if this joint has no deform mesh >> snap to previous joint

# if script still fails then unparent joint first - place - then parent joints back into the system
def placeFitJointIntoPlace():
    global torsoFitJoints

    global originalBodyMeshes

    # pair = [deformJointName, deformJointMesh]
    global pairJointsMeshesGlobal

    # auto reload in case the pairList got empty
    autoReloadPairJointsMeshesGlobal()

    # sort pairJointsMeshesGlobal >> this is not enough, need to unParent then parent them back
    sortPairJointsMeshesGlobal()

    # merge vertices to make sure
    mergeVertices_deformJointMeshes()

    # loop through pairJointsMeshesGlobal >> get fitJointName
    # only need Right and Middle pair only
    for pair in pairJointsMeshesGlobal:
        print(pair)
        if not cmds.objExists(pair[1]):
            print(pair[1]+" does not exist")
        else:
            fitJoint_and_Side = getFitJointNameFromDeformJointName(pair[0])
            fitJointName = fitJoint_and_Side[0]
            # skip left side
            if fitJoint_and_Side[1] == "_L":
                pass
            else:
                # find previous deformJointMesh
                previousDeformJointMesh = detectPreviousDeformJointMesh(fitJointName)
                # identify position for fitJoint
                if previousDeformJointMesh:
                    fitJointPos = getFitJointPosition(fitJointName, pair[1], previousDeformJointMesh)
                    print(fitJointPos)
                    if cmds.objExists(fitJointName):
                        cmds.xform(fitJointName, t=fitJointPos, ws=1)
                        cmds.refresh()
                elif torsoFitJoints and fitJointName == torsoFitJoints[0]:
                    if cmds.objExists(pair[1]):
                        cmds.xform(pair[1], cp=1)
                        fitJointPos = cmds.xform(pair[1], q=1, rp=1, ws=1)
                        if cmds.objExists(fitJointName):
                            cmds.xform(fitJointName, t=fitJointPos, ws=1)
                            cmds.refresh()

    # place end joints
    placeEndJointIntoPlace()

    # place eye joints into custom locations
    placeEyeFitJointCustomLocation()

    cmds.select(clear=1)
    cmds.hide("dupMeshesForCut_Grp")
    cmds.showHidden("deformJointMeshes_Grp")

def fixPoleVectorProcess(footOrHandFitJointsGlobal):
    global torsoFitJoints
    # find middle X between 3 joints
    # apply this X for all 3 joints (un-parent then move then parent them back)
    for ankle in footOrHandFitJointsGlobal:
        knee = cmds.listRelatives(ankle, parent=1)[0]
        hip = cmds.listRelatives(knee, parent=1)[0]

        hipPos = cmds.xform(hip, q=1, t=1, ws=1)

        # find ratio to find new distance
        distanceKneeHipCurrent = distanceBetweenTwoPoints(knee, hip)
        distanceAnkleKneeCurrent = distanceBetweenTwoPoints(ankle, knee)
        ratio = distanceKneeHipCurrent/(distanceKneeHipCurrent+distanceAnkleKneeCurrent)

        # new distance
        distanceAnkleHip = distanceBetweenTwoPoints(ankle, hip)
        newDistanceKneeHip = ratio*distanceAnkleHip

        # move Knee under Root joint
        cmds.parent(knee, torsoFitJoints[0])

        # move Ankle under Hip joint
        cmds.parent(ankle, hip)

        # turn on fit mode to update orientation (between hip and ankle). Hip (and Ankle) is master
        mel.eval('asFitModeManualUpdate')

        # snap "Knee" to "Hip"
        cmds.xform(knee, t=hipPos, ws=1)
        cmds.parent(knee, hip)

        # turn on fit mode to update orientation between knee and hip (hip is still master)
        mel.eval('asFitModeManualUpdate')

        # move knee out. Minus value (-X)
        cmds.xform(knee, t=[newDistanceKneeHip, 0, 0], r=1)

        # parent ankle back under knee
        cmds.parent(ankle, knee)

        # update orientation again
        mel.eval('asFitModeManualUpdate')

        if footOrHandFitJointsGlobal == footFitJointsGlobal:
            # check again to avoid flipping
            placeKneeJoints()

        elif footOrHandFitJointsGlobal == handFitJointsGlobal:
            placeElbowJoints()

        cmds.select(clear=1)

# unstable. Hip rotation jump when do Update orientation even it already face forward.
def fixPoleVector():
    # global footFitJointsGlobal
    # global handFitJointsGlobal
    # if handFitJointsGlobal:
    #     fixPoleVectorProcess(handFitJointsGlobal)
    # if footFitJointsGlobal:
    #     fixPoleVectorProcess(footFitJointsGlobal)
    pass

def buildAdvancedSkeleton():
    mel.eval('asReBuildAdvancedSkeleton')
    cmds.hide('eyesLocator_Grp')
    cmds.hide('faceItems_Grp')
    # cmds.showHidden("originalBodyMeshes_Grp")

def toggleFitAdv():
    mel.eval('asToggleFitAdvancedSkeleton')

def checkInbetweenAndTwistJointsFromDeformJoint(deformJointName):
    fitJointNameAndSide = getFitJointNameFromDeformJointName(deformJointName)
    fitJointName = fitJointNameAndSide[0]
    side = fitJointNameAndSide[1]
    attrTwistExist = cmds.attributeQuery("twistJoints", node=fitJointName, exists=True)
    if attrTwistExist:
        newJointList = []
        newJointList.append(deformJointName)
        jointNum = cmds.getAttr(fitJointName+".twistJoints")
        for num in range(jointNum):
            partJoint = fitJointName+"Part"+str(num+1)+side
            newJointList.append(partJoint)
        print(newJointList)
        return newJointList

    attrInbetweenExist = cmds.attributeQuery("inbetweenJoints", node=fitJointName, exists=True)
    if attrInbetweenExist:
        newJointList = []
        newJointList.append(deformJointName)
        jointNum = cmds.getAttr(fitJointName + ".inbetweenJoints")
        for num in range(jointNum):
            partJoint = fitJointName+"Part"+str(num+1)+side
            newJointList.append(partJoint)
        print(newJointList)
        return newJointList

        return jointNum
    return None

# backup and create proxy mesh
def backupDeformJointMesh(mesh):
    backupMesh = cmds.duplicate(mesh, name=mesh+"_proxy")[0]
    cmds.parent(backupMesh, "dupMeshesForCut_Grp")
    return backupMesh

def autoUV():
    global mainBodyMesh
    global nonDeformedProps
    if mainBodyMesh and nonDeformedProps:
        # check if uv is available
        mainBodyMeshFaces = mainBodyMesh+".f[*]"
        # cmds.select(mainBodyMeshFaces)
        mainBodyMesheUV = cmds.polyListComponentConversion(mainBodyMeshFaces, fromFace=1, toUV=1)
        if not mainBodyMesheUV:
            cmds.polyAutoProjection(mainBodyMesh, ch=0)
            cmds.select(clear=1)

def cleanUpDeformJointMeshes_Grp():
    if cmds.objExists("deformJointMeshes_Grp"):
        # clean up empty group
        childrenOfdeformJointMeshes_Grp = cmds.listRelatives("deformJointMeshes_Grp", children=1)
        deleteList = []
        for child in childrenOfdeformJointMeshes_Grp:
            if cmds.nodeType(child) == 'transform':
                children = cmds.listRelatives(child, c=True)
                if children == None:
                    deleteList.append(child)
        cmds.delete(deleteList)

def bindDeformJointMeshesToDeformJoints_then_CopySkin():
    global pairJointsMeshesGlobal
    global bindingJointsList
    global originalBodyMeshes
    global proxyMeshes
    proxyMeshes = []
    bindingJointsList = []
    deformMeshesList = []

    # delete history all
    mel.eval("DeleteAllHistory;")

    # clean up empty group under deformJointMeshes_Grp
    cleanUpDeformJointMeshes_Grp()

    # autoUV in case of non-deformed props and bodymesh has no Uv
    autoUV()

    print(pairJointsMeshesGlobal)
    for pair in pairJointsMeshesGlobal:
        print(pair)
        # if deform joints or deform joint mesh does not exist >> skip
        if cmds.objExists(pair[0]) and cmds.objExists(pair[1]):
            # clean skin cluster first
            cmds.delete(pair[1], ch=1)
            print("Binding "+str(pair))
            newJointList = checkInbetweenAndTwistJointsFromDeformJoint(pair[0])
            # working here
            proxyMesh = backupDeformJointMesh(pair[1])
            proxyMeshes.append(proxyMesh)

            if not newJointList:
                try:
                    cmds.skinCluster(pair[0], pair[1], sm=0, tsb=True)
                except:
                    print("This "+str(pair[1])+" already has skincluster")
                bindingJointsList.append(pair[0])
                deformMeshesList.append(pair[1])

            else:
                try:
                    cmds.skinCluster(newJointList, pair[1], sm=0, tsb=True)
                except:
                    print("This "+str(pair[1])+" already has skincluster")
                bindingJointsList.extend(newJointList)
                deformMeshesList.append(pair[1])

    print(bindingJointsList)
    print(deformMeshesList)
    # combine all deformJointMeshes with combine skincluster checked
    if deformMeshesList:
        # this is to avoid deleting deformJointMeshes_Grp
        # cmds.parent(deformMeshesList, world=1)
        # only available from Maya 2017
        mergedDeformMesh = cmds.polyUniteSkinned(deformMeshesList, ch=0)[0]
        print(mergedDeformMesh)

        # find skinCluster in the merged deform mesh
        mergedSkin = mel.eval('findRelatedSkinCluster ' + mergedDeformMesh)

        # bind skin on original meshes
        for mesh in originalBodyMeshes:
            if cmds.objExists(mesh):
                oriSkin = cmds.skinCluster(bindingJointsList, mesh, sm=0, tsb=True)[0]
                # copy skin weight from the mergedDeformMesh to the original mesh
                cmds.copySkinWeights(ss=mergedSkin, ds=oriSkin, nm=True, surfaceAssociation='closestPoint')

        # parent it back to TRCR for organization
        cmds.parent(mergedDeformMesh, "TRCR_Grp")
        # hide mergedDeformMesh
        cmds.hide(mergedDeformMesh)
        cmds.showHidden("originalBodyMeshes_Grp")
        cmds.hide("dupMeshesForCut_Grp")
        try:
            cmds.hide("deformJointMeshes_Grp")
        except:
            print("deformJointMeshes_Grp is gone")

        cleanUpEmptyGroups('originalBodyMeshes_Grp')
        createStructure()

    return bindingJointsList

def ngSkinRelax(MllInterface, skinned_mesh, relax_num=1):
    '''
    Require ngSkinTools already installed
    :param class MllInterface: from ngSkinTools Python API module
    :param str skinned_mesh: name of the mesh of which skinWeights are to be relaxed
    '''
    ngSkin_MLL = MllInterface()

    ngSkin_MLL.setCurrentMesh(skinned_mesh)
    ngSkin_MLL.initLayers()
    relax_layer = ngSkin_MLL.createLayer('Relax')

    for i in range(relax_num):
        cmds.ngSkinRelax(skinned_mesh)

def setSmoothTime():
    global smoothTime
    global smoothTimeField
    smoothTime = cmds.intField(smoothTimeField, q=1, v=1)
    if smoothTime < 0:
        raise Exception("Smooth time need to be > 0")
    print(smoothTime)
    return smoothTime

def smoothSkinning(MllInterface, orginalBodyMeshes, relax_num=1):
    # Only proceed if ngSkinTools module has been successfully imported
    if MllInterface and originalBodyMeshes:
        if relax_num:
            for mesh in originalBodyMeshes:
                ngSkinRelax(MllInterface, mesh, relax_num)
            # smooth merged version as well

    # Cleanup
    try:
        LayerUtils.deleteCustomNodes() # type: ignore
    except ImportError:
        # TODO: manually clean up the ngSkinData node connected to the skinCluster node
        pass

def lauchNgSkinTool():
    from ngSkinTools.ui.mainwindow import MainWindow
    MainWindow.open()

def createProxyRig():
    global proxyMeshes
    if not proxyMeshes:
        print("proxyMeshes variable has no value")

    # create proxy folder
    if not cmds.objExists("Proxy_Meshes"):
        cmds.group(name="Proxy_Meshes", em=1)
        # add layer here
        existingLayers = cmds.ls(type="displayLayer")
        proxyLayerName = "Proxy_Geo_Layer"
        if proxyLayerName not in existingLayers:
            proxyLayer = cmds.createDisplayLayer("Proxy_Meshes", name=proxyLayerName)
            cmds.setAttr("{}.displayType".format(proxyLayer), 2)  # Change layer to reference.
            cmds.setAttr("{}.visibility".format(proxyLayer), 0)
        else:
            cmds.select("Proxy_Meshes", r=1)
            mel.eval('layerEditorAddObjects {}'.format(proxyLayerName))

        if cmds.objExists("Group"):
            cmds.parent("Proxy_Meshes", "Group")

    for proxyMesh in proxyMeshes:
        deformJointName = proxyMesh.split("_Mesh_proxy")[0]
        if cmds.objExists(proxyMesh) and cmds.objExists(deformJointName):
            cmds.delete(proxyMesh, ch=1)
            cmds.parent(proxyMesh, "Proxy_Meshes")

            cmds.skinCluster(deformJointName, proxyMesh, sm=0, tsb=True)
    cmds.select(clear=1)

###################################
# Adjust Control Curves functions #
###################################

# use distance from fit joint/ centerPos to the closest vertex for control size
def getRadiusFromFitJointToDeformJointMesh(deformJoint, deformJointMesh):
    distance = None
    if cmds.objExists(deformJoint) and cmds.objExists(deformJointMesh):
        closestVer = findClosestVerOnMesh_to_Point(deformJoint, deformJointMesh)
        if closestVer:
            distance = distanceBetweenTwoPoints(closestVer, deformJoint)
            return distance
    return distance

def yellowcon(curve):
    s = cmds.listRelatives(curve, children=1, shapes=1)[0]
    if s:
        cmds.setAttr(s+'.overrideEnabled', 1)
        cmds.setAttr(s+'.overrideColor', 17)

def greencon(curve):
    s = cmds.listRelatives(curve, children=1, shapes=1)[0]
    if s:
        cmds.setAttr(s+'.overrideEnabled', 1)
        cmds.setAttr(s+'.overrideColor', 14)

def redcon(curve):
    s = cmds.listRelatives(curve, children=1, shapes=1)[0]
    if s:
        cmds.setAttr(s+'.overrideEnabled', 1)
        cmds.setAttr(s+'.overrideColor', 13)

def pinkcon(curve):
    s = cmds.listRelatives(curve, children=1, shapes=1)[0]
    if s:
        cmds.setAttr(s+'.overrideEnabled', 1)
        cmds.setAttr(s+'.overrideColor', 20)

def lightblue(curve):
    s = cmds.listRelatives(curve, children=1, shapes=1)[0]
    if s:
        cmds.setAttr(s+'.overrideEnabled', 1)
        cmds.setAttr(s+'.overrideColor', 18)

def lightgreen(curve):
    s = cmds.listRelatives(curve, children=1, shapes=1)[0]
    if s:
        cmds.setAttr(s+'.overrideEnabled', 1)
        cmds.setAttr(s+'.overrideColor', 19)

# Scapular >> FKScapula_R, FKScapula_L. Need a better shape
def createFKCircleCurve(fitJointName):
    global meshesSize
    deformJointList = getDeformJointFromFitJoint(fitJointName)
    for deformJoint in deformJointList:
        # FKs
        fkControlName = "FK"+deformJoint+"_template"
        deformJointMesh = deformJoint+"_Mesh"
        if cmds.objExists(deformJointMesh):
            distance = getRadiusFromFitJointToDeformJointMesh(deformJoint, deformJointMesh)
            if cmds.objExists("FK"+deformJoint+"_template"):
                cmds.delete("FK"+deformJoint+"_template")
            cmds.select(clear=1)
            if distance:
                if meshesSize:
                    # if the control is too big, scale it down. Else, if control is too small, scale it up
                    if distance > meshesSize[1]/10 or distance < meshesSize[1]/300:
                        distance = meshesSize[1]/10
                fkCircleCon = cmds.circle(name=fkControlName, radius=distance*2, normal=[0, 1, 0], ch=0)[0]
                cmds.parent(fkCircleCon, "curveTemplates_Grp")
                if deformJoint.endswith("_R"):
                    redcon(fkCircleCon)
                elif deformJoint.endswith("_L"):
                    greencon(fkCircleCon)
                else:
                    lightblue(fkCircleCon)

# IKs:
def createBBoxCurve(curve_name, deformJoint, deformJointMesh, offsetX=1, offsetY=1, offsetZ=1):
    global meshesSize
    minX = None

    if not cmds.objExists(deformJointMesh):
        if meshesSize:
            print("using model size for control size")
            minX = -(meshesSize[1]/10)
            minY = -(meshesSize[1]/10)
            minZ = -(meshesSize[1]/10)
            maxX = meshesSize[1]/10
            maxY = meshesSize[1]/10
            maxZ = meshesSize[1]/10
    else:
        print("using deformJointMesh BBox for control size")
        # create curve based on bounding box of deformJointMesh
        bBox = cmds.exactWorldBoundingBox(deformJointMesh)
        print(bBox)
        minX = bBox[0]
        minY = bBox[1]
        minZ = bBox[2]
        maxX = bBox[3]
        maxY = bBox[4]
        maxZ = bBox[5]

    # just to make sure it has size
    print("This is min value " + str(minX))
    if minX and cmds.objExists(deformJoint):

        boxCurve = cmds.curve(name=curve_name, degree=1,\
                    knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],\
                    point=[(minX, maxY, minZ),\
                             (minX, maxY, maxZ),\
                             (maxX, maxY, maxZ),\
                             (maxX, maxY, minZ),\
                             (minX, maxY, minZ),\
                             (minX, minY, minZ),\
                             (minX, minY, maxZ),\
                             (maxX, minY, maxZ),\
                             (maxX, maxY, maxZ),\
                             (minX, maxY, maxZ),\
                             (minX, minY, maxZ),\
                             (minX, minY, minZ),\
                             (maxX, minY, minZ),\
                             (maxX, maxY, minZ),\
                             (maxX, maxY, maxZ),\
                             (maxX, minY, maxZ),\
                             (maxX, minY, minZ)]\
                  )
        print(boxCurve)
        pinkcon(boxCurve)
        cmds.parent(boxCurve, "curveTemplates_Grp")

        if not cmds.objExists(deformJointMesh):
            print("This "+deformJointMesh+" does not exist")
        else:
            # use joint location as pivot
            deformJointPos = cmds.xform(deformJoint, q=1, t=1, ws=1)
            cmds.xform(boxCurve, pivots=deformJointPos, ws=1)

            # move curve to origin then freeze transform
            tempGrp = cmds.group(empty=1, world=1)
            pointConst = cmds.pointConstraint(tempGrp, boxCurve, mo=0)
            cmds.delete(pointConst)
            cmds.delete(tempGrp)
            # scale Z to make it a bit bigger
            currentScale = cmds.xform(boxCurve, q=1, s=1, r=1)
            cmds.xform(boxCurve, s=[currentScale[0]*offsetX, currentScale[1]*offsetY, currentScale[2]*offsetZ])

            cmds.makeIdentity(boxCurve, apply=True, t=1, r=1, s=1, n=0)
        return boxCurve
    else:
        print("dont have enough variables to create control template")

# create box control based on deformJointMesh
# box: IKSpine1_M, IKLeg*_R, IKArm*_R
def createBoxControls(fitJointsList):
    global meshesSize
    if fitJointsList == footFitJointsGlobal:
        name = "Leg"
        offsetX = 1.3
        offsetY = 1
        offsetZ = 1.6
    elif fitJointsList == handFitJointsGlobal:
        name = "Arm"
        offsetX = 2
        offsetY = 2
        offsetZ = 2
    elif fitJointsList == torsoFitJoints:
        name = "Spine"
        if meshesSize:
            # if model is standing up (2 legs usually)
            if meshesSize[1] > meshesSize[2]:
                offsetX = 1.2
                offsetY = 0.2
                offsetZ = 1.2

            # usually 4 legs
            elif meshesSize[1] < meshesSize[2]:
                offsetX = 1.2
                offsetY = 1.2
                offsetZ = 0.2
            else:
                offsetX = 1.2
                offsetY = 1.2
                offsetZ = 1.2
        # if no meshesSize >> scale all direction
        else:
            offsetX = 1.2
            offsetY = 1.2
            offsetZ = 1.2

    for fitJointName in fitJointsList:
        deformJointList = getDeformJointFromFitJoint(fitJointName)
        side = None
        for deformJoint in deformJointList:
            print(deformJoint)
            if deformJoint.endswith("_R"):
                side = "_R"
            elif deformJoint.endswith("_L"):
                side = "_L"
            elif deformJoint.endswith("_M"):
                side = "_M"

            if fitJointsList == footFitJointsGlobal:
                if len(fitJointsList) == 1:
                    ikConName = "IK" + name + side + "_template"
                    if cmds.objExists("IK" + name + side + "_template"):
                        cmds.delete("IK" + name + side + "_template")
                    createBBoxCurve(ikConName, deformJoint, deformJoint + "_Mesh", offsetX, offsetY, offsetZ)

                # adding Front
                elif len(fitJointsList) == 2:
                    indexNum = fitJointsList.index(fitJointName)
                    if indexNum == 0:
                        ikConName = "IK" + name + side + "_template"
                        if cmds.objExists("IK" + name + side + "_template"):
                            cmds.delete("IK" + name + side + "_template")
                        createBBoxCurve(ikConName, deformJoint, deformJoint + "_Mesh", offsetX, offsetY, offsetZ)
                    else:
                        ikConName = "IK" + name + "Front" + side + "_template"
                        if cmds.objExists("IK" + name + "Front" + side + "_template"):
                            cmds.delete("IK" + name + "Front" + side + "_template")
                        createBBoxCurve(ikConName, deformJoint, deformJoint + "_Mesh", offsetX, offsetY, offsetZ)

                # adding Front + indexNum
                elif len(fitJointsList) > 2:
                    indexNum = fitJointsList.index(fitJointName)
                    if indexNum == 0:
                        ikConName = "IK" + name + side + "_template"
                        if cmds.objExists("IK" + name + side + "_template"):
                            cmds.delete("IK" + name + side + "_template")
                        createBBoxCurve(ikConName, deformJoint, deformJoint + "_Mesh", offsetX, offsetY, offsetZ)
                    else:
                        ikConName = "IK" + name + "Front" + str(indexNum) + side + "_template"
                        if cmds.objExists("IK" + name + "Front" + str(indexNum) + side + "_template"):
                            cmds.delete("IK" + name + "Front" + str(indexNum) + side + "_template")
                        createBBoxCurve(ikConName, deformJoint, deformJoint + "_Mesh", offsetX, offsetY, offsetZ)
            else:
                if len(fitJointsList) > 1:
                    indexNum = fitJointsList.index(fitJointName)+1
                    ikConName = "IK" + name + str(indexNum) + side + "_template"
                    if cmds.objExists("IK" + name + str(indexNum) + side + "_template"):
                        cmds.delete("IK" + name + str(indexNum) + side + "_template")
                    createBBoxCurve(ikConName, deformJoint, deformJoint+"_Mesh", offsetX, offsetY, offsetZ)

                elif len(fitJointsList) == 1:
                    ikConName = "IK" + name + side + "_template"
                    if cmds.objExists("IK" + name + side + "_template"):
                        cmds.delete("IK" + name + side + "_template")
                    createBBoxCurve(ikConName, deformJoint, deformJoint + "_Mesh", offsetX, offsetY, offsetZ)


# Root >> IKSpine1_M, HipSwinger_M, RootX_M, IKhybridSpine1_M (box, gear, 4arrows, star)
# Mid >> IKSpine2_M, IKhybridSpine2_M  (box, star)
# Chest >> IKSpine3_M, IKhybridSpine3_M (box, star)

# Foot >> IKLeg*_R, IKLeg*_L (box), poleVector?. * is number, start from 1
# Arm >> IKArm*_R, IKArm*_L (box), poleVector?

# Toes >> IKToes_L, IKToes_R, RollToes_R, RollToes_L (square, gear)
# ToesEnd >> RollToesEnd_L, RollToesEnd_R (gear)
# Heel >> RollHeel_L, RollHeel_R (gear)

# Knee >> PoleLeg_R, PoleLeg_L (locator)
# Elbow >> PoleArm_R, PoleArm_L (locator)

# Hip - Foot >> FKIKLeg_R, FKIKLeg_L (plus)

# Shoulder - Hand >> FKIKArm_R, FKIKArm_L (plus)
# Root-Chest >> FKIKSpine_M (plus)
# 0-1-2... >> IKSpline*_M, IKhybridSpline*_M, FKIKSpline*_M . * is IKLabel name (box, star, plus)

# Eye >> AimEye_M, AimEye_R, AimEye_L (circle, infinity) >> no need for now

# all the IKFK switches not go inside meshes but not too far from the mesh >> how to solve that?


# universal scale all the control under MotionSystem
# >> based on nearest deformJointMesh vs the control
# >> nearest vertex on this mesh = size
# >> find BBoxY of current control. size/BBoxY = Scale
# (not a correct way but hopefully get everything done. Check back later)
# >> control scale using MeshesSize
def autoSetupPivotDeformJointMeshesList():
    global deformJointMeshesList
    if deformJointMeshesList:
        for deformJointMesh in deformJointMeshesList:
            deformJoint = deformJointMesh[:-5]
            if cmds.objExists(deformJoint):
                pos=cmds.xform(deformJoint, q=1, rp=1, ws=1)
                cmds.xform(deformJointMesh, pivots=pos)

def findClosestObjectInList_to_mainFirstObject(mainFirstObj, listOfObjects):
    closestDistance = 9999999
    closestItem = None
    for item in listOfObjects:
        distance = distanceBetweenTwoPointsRP(mainFirstObj, item)
        if distance <= closestDistance:
            closestDistance = distance
            closestItem = item
    return closestItem


def scaleControlCVs(controlName, scaleNum, closestDeformJoint=None):
    curveShapes = cmds.listRelatives(controlName, children=1, shapes=1)
    if curveShapes:
        curveShape = curveShapes[0]
        curveCV = curveShape + ".cv[0:99999999]"
        if closestDeformJoint:
            pos = cmds.xform(closestDeformJoint, q=1, rp=1, ws=1)
        else:
            cmds.select(curveCV, r=1)
            cmds.refresh()
            cmds.setToolTo('Move')
            pos = cmds.manipMoveContext("Move", q=1, p=1)
        cmds.xform(curveCV, a=1, scalePivot=pos, scale=(scaleNum, scaleNum, scaleNum))

def maxAllDirectionBBoxMeshes(obj):
    maxSize = None
    objShapes = cmds.listRelatives(obj, children=1, shapes=1)
    if objShapes:
        objShape = objShapes[0]
        if objShape:
            objBBox = cmds.exactWorldBoundingBox(objShape)

            maxXMesh = objBBox[3]
            minXMesh = objBBox[0]
            xSize = maxXMesh - minXMesh

            maxYMesh = objBBox[4]
            minYMesh = objBBox[1]
            ySize = maxYMesh - minYMesh

            maxZMesh = objBBox[5]
            minZMesh = objBBox[2]
            zSize = maxZMesh - minZMesh

            maxSize = max([xSize, ySize, zSize])
            return maxSize

def universallyScaleControls(allControlCurves):
    global meshesSize
    global deformJointMeshesList
    global originalBodyMeshes

    if not meshesSize:
        if originalBodyMeshes:
            getOriginalBodyMeshesSize(originalBodyMeshes)
        else:
            print("originalBodyMeshes is not defined")

    if not deformJointMeshesList:
        autoReloadPairJointsMeshesGlobal()

    # >> need to run and define them again

    # setup pivot for findClosestDeformJointMesh
    autoSetupPivotDeformJointMeshesList()

    skipTheseControls = []
    nameList = ["HipSwinger", "AimEye", "FKIKArm", "FKIKLeg", "FKIKSpline", "Root", "FKIKSpine"]
    for controlCurve in allControlCurves:
        for name in nameList:
            if controlCurve.startswith(name):
                skipTheseControls.append(controlCurve)
    print(skipTheseControls)

    deformJointList = []

    if deformJointMeshesList and allControlCurves:
        if cmds.objExists("DeformationSystem"):
            deformJointList = cmds.listRelatives("DeformationSystem", children=1, ad=1)

        for controlCurve in allControlCurves:
            print(controlCurve)
            if controlCurve not in skipTheseControls:
                # find closest deformJointMesh to this control curve
                if deformJointList:
                    closestDeformJoint = findClosestObjectInList_to_mainFirstObject(controlCurve, deformJointList)
                    print(closestDeformJoint)
                    fitJointName_n_side = getFitJointNameFromDeformJointName(closestDeformJoint)
                    fitJointName = fitJointName_n_side[0]
                    side = fitJointName_n_side[1]
                    closestDeformJointMesh = fitJointName+side+"_Mesh"

                    if not cmds.objExists(closestDeformJointMesh):
                        fitJointName = getFitJointNameFromDeformJointName(closestDeformJoint)[0]
                        if cmds.objExists(fitJointName):
                            closestDeformJointMesh = detectPreviousDeformJointMesh(fitJointName)
                        else:
                            print(closestDeformJointMesh+" does not exist")

                    if closestDeformJointMesh and cmds.objExists(closestDeformJointMesh):
                        print(closestDeformJointMesh)
                        # find closest vertex on deformJointMesh to this control curve
                        nearestVer = findClosestVerOnMesh_to_Point(controlCurve, closestDeformJointMesh)
                        nearestVerPos = cmds.xform(nearestVer, q=1, t=1, ws=1)

                        controlCurvePos = cmds.xform(controlCurve, q=1, rp=1, ws=1)

                        # find distance from the closest vertex on deformJointMesh to this control curve
                        size = distanceBetweenTwoPositions(controlCurvePos, nearestVerPos)
                        if meshesSize:
                            if size < meshesSize[1]/200:
                                print("distance is too small, now use meshesSize for control size")
                                size = meshesSize[1]/10
                            if size >= meshesSize[1]/2:
                                print("distance is too big, now use meshesSize for control size")
                                size = meshesSize[1]/10
                        # *num because size was counted from the joint (center)
                        size = size*3.5
                        print("size is " + str(size))

                        bBoxSize = maxAllDirectionBBoxMeshes(controlCurve)
                        print("bBox is " + str(bBoxSize))

                        if size and bBoxSize:
                            scaleNum = size/bBoxSize
                            print(scaleNum)
                            scaleControlCVs(controlCurve, scaleNum, closestDeformJoint)
                    cmds.refresh()

def adjustPoleVectorControls(allControlCurves):
    global meshesSize
    poleSize = meshesSize[1]/15

    poleVectorControls = []
    for controlCurve in allControlCurves:
        if controlCurve.startswith("Pole"):
            poleVectorControls.append(controlCurve)

    for poleVectorControl in poleVectorControls:
        bBoxSize = maxAllDirectionBBoxMeshes(poleVectorControl)
        scaleNum = poleSize/bBoxSize
        scaleControlCVs(poleVectorControl, scaleNum, None)

def adjustRootControls():
    # HipSwinger >> near RootDeformJointMesh + RootJoint
    global torsoFitJoints
    global meshesSize

    if meshesSize:
        hipSwingerSize = meshesSize[1]/15
        bBoxSize = maxAllDirectionBBoxMeshes("HipSwinger_M")
        scaleNum = hipSwingerSize / bBoxSize
        scaleControlCVs("HipSwinger_M", scaleNum, None)

    fitJointsNearHipSwinger = None

    if firstLegFitJointsGlobal:
        fitJointsNearHipSwinger = firstLegFitJointsGlobal
    elif torsoFitJoints:
        fitJointsNearHipSwinger = torsoFitJoints

    if fitJointsNearHipSwinger:
        closestFitJoint = findClosestObjectInList_to_mainFirstObject("HipSwinger_M", fitJointsNearHipSwinger)
        # do right side only, left side mirror over
        closestDeformJoint = getDeformJointFromFitJoint(closestFitJoint)[0]
        closestDeformJointMesh = closestDeformJoint + "_Mesh"
        if not cmds.objExists(closestDeformJointMesh):
            closestDeformJointMesh = detectPreviousDeformJointMesh(closestFitJoint)
        print(closestDeformJointMesh)
        bBoxDeformJointMesh = cmds.exactWorldBoundingBox(closestDeformJointMesh)
        minX = bBoxDeformJointMesh[0]
        print(minX)

        curveShapes = cmds.listRelatives("HipSwinger_M", children=1, shapes=1)
        if curveShapes:
            curveShape = curveShapes[0]
            curveCV = curveShape + ".cv[0:99999999]"
            cmds.select(curveCV, r=1)
            cmds.refresh()
            cmds.setToolTo('Move')
            pos = cmds.manipMoveContext("Move", q=1, p=1)
            print(pos)
            if pos[0] < 0:
                distance = (minX - pos[0])*0.9
                print(distance)
                if distance:
                    cmds.xform(curveCV, r=1, t=[0, 0, distance])

    # create RootX_M_template
    if cmds.objExists("RootX_M_template"):
        cmds.delete("RootX_M_template")

    if meshesSize:
        # if model is standing up (2 legs usually)
        if meshesSize[1] > meshesSize[2]:
            print('This one is 2 legs')
            offsetX = 1.5
            offsetY = 0.3
            offsetZ = 1.5

        # usually 4 legs
        elif meshesSize[1] < meshesSize[2]:
            print('This one is 4 legs')
            offsetX = 1.5
            offsetY = 1.5
            offsetZ = 0.3
        else:
            print('This one is a box?')
            offsetX = 1.5
            offsetY = 1.5
            offsetZ = 1.5
    # if no meshesSize >> scale all direction
    else:
        print('MeshesSize is not available')
        offsetX = 1.5
        offsetY = 1.5
        offsetZ = 1.5

    if cmds.objExists(torsoFitJoints[0]):
        rootDeformJoint = getDeformJointFromFitJoint(torsoFitJoints[0])[0]
        rootDeformJointMeshBBox = cmds.exactWorldBoundingBox(rootDeformJoint+"_Mesh")
        rootDeformJointMeshBBox_xSize = rootDeformJointMeshBBox[3]-rootDeformJointMeshBBox[0]
        if meshesSize:
            # if meshesSize available, scale RootX_M control to match X size of the model
            offsetX = (meshesSize[0]/rootDeformJointMeshBBox_xSize)*1.2

        rootCon = createBBoxCurve("RootX_M_template", rootDeformJoint, rootDeformJoint+"_Mesh", offsetX, offsetY, offsetZ)
        yellowcon(rootCon)

# # testing
# allControlCurves = []
# if cmds.objExists("MotionSystem"):
#     allControls = cmds.listRelatives("MotionSystem", children=1, ad=1)
#     for item in allControls:
#         if cmds.nodeType(item) == 'transform':
#             itemShapeList = cmds.listRelatives(item, children=1, shapes=1)
#             if itemShapeList:
#                 if cmds.nodeType(itemShapeList[0]) == 'nurbsCurve':
#                     allControlCurves.append(item)
#
# for con in allControlCurves:
#     moveFKIKBlendControlCVs(con)

def moveFKIKBlendControlCVs(controlName):
    global deformJointMeshesList

    if not deformJointMeshesList:
        autoReloadPairJointsMeshesGlobal()

    if controlName.startswith("FKIKLeg") or controlName.startswith("FKIKArm") or controlName.startswith("FKIKSpline") or controlName.startswith("FKIKSpine"):
        if controlName.endswith("_R") or controlName.endswith("_M"):
            closestDeformJointMesh = findClosestObjectInList_to_mainFirstObject(controlName, deformJointMeshesList)
            if closestDeformJointMesh:
                print(closestDeformJointMesh)
                bBoxDeformJointMesh = cmds.exactWorldBoundingBox(closestDeformJointMesh)
                minX = bBoxDeformJointMesh[0]*1.3
                print("minX is" + str(minX))
                curveShapes = cmds.listRelatives(controlName, children=1, shapes=1)
                if curveShapes:
                    curveShape = curveShapes[0]
                    curveCV = curveShape + ".cv[0:99999999]"
                    cmds.select(curveCV, r=1)
                    cmds.refresh()
                    cmds.setToolTo('Move')
                    pos = cmds.manipMoveContext("Move", q=1, p=1)
                    print("control position is " + str(pos))
                    if pos[0] < 0:
                        distance = (minX-pos[0])
                    elif pos[0] > 0:
                        distance = -(pos[0] - minX)
                    print("distance is " + str(distance))
                    if distance:
                        cmds.xform(curveCV, r=1, t=[distance, 0, 0])
                        print("moved "+controlName+" out")
    cmds.select(clear=1)

def adjustBlendIKFKControls(allControlCurves):
    # adjust size based on MeshesSize
    # move ikfkBlend to joint chain + deformJointMesh
    global meshesSize
    fkIKSize = meshesSize[1]/12

    fkIKControls = []
    for controlCurve in allControlCurves:
        if controlCurve.startswith("FKIK"):
            fkIKControls.append(controlCurve)

    for fkIKControl in fkIKControls:
        bBoxSize = maxAllDirectionBBoxMeshes(fkIKControl)
        scaleNum = fkIKSize/bBoxSize
        scaleControlCVs(fkIKControl, scaleNum, None)
        moveFKIKBlendControlCVs(fkIKControl)

def moveControlOutOfMesh(fitJointsList):
    global meshesSize
    if not meshesSize:
        if originalBodyMeshes:
            getOriginalBodyMeshesSize(originalBodyMeshes)
        else:
            print("originalBodyMeshes is not defined")

    if fitJointsList == headFitJointsGlobal:
        if meshesSize[1] > meshesSize[2]:
            direction = "X"
        else:
            direction = "-Y"
    else:
        direction = "X"

    for fitJoint in fitJointsList:
        deformJoint = getDeformJointFromFitJoint(fitJoint)[0] # right or middle only is enough
        deformJointMesh = deformJoint + "_Mesh"
        if not cmds.objExists(deformJointMesh):
            deformJointMesh = detectPreviousDeformJointMesh(fitJoint)
        print(deformJointMesh)
        if deformJointMesh:
            bBoxDeformJointMesh = cmds.exactWorldBoundingBox(deformJointMesh)
            maxX = bBoxDeformJointMesh[3]
            print(maxX)
            maxY = bBoxDeformJointMesh[4]
            print(maxY)
            maxZ = bBoxDeformJointMesh[5]
            print(maxZ)

            fkControlName = "FK" + deformJoint

            if cmds.objExists(fkControlName):
                pinkcon(fkControlName)
                curveShapes = cmds.listRelatives(fkControlName, children=1, shapes=1)
                if curveShapes:
                    curveShape = curveShapes[0]
                    curveCV = curveShape + ".cv[0:99999999]"
                    cmds.select(curveCV, r=1)
                    cmds.refresh()
                    cmds.setToolTo('Move')
                    pos = cmds.manipMoveContext("Move", q=1, p=1)
                    print(pos)

                    distance = 0
                    # when -X will happen? I'm confused. Last rig, the head work with -X
                    if direction == "-X":
                        # joint axis = -X for head means Y in model's axis
                        distance = (maxY - pos[1])*1.4
                        print("distance is " + str(distance))
                        cmds.xform(curveCV, r=1, t=[-distance, 0, 0])
                    elif direction == "X":
                        # joint's axis = X for jaw means Z in model's axis
                        distance = (maxZ - pos[2])*1.4
                        print("distance is " + str(distance))
                        cmds.xform(curveCV, r=1, t=[distance, 0, 0])
                    elif direction == "-Y":
                        # this is for 4 legs. -Y in joint axis = Y in model's axis
                        distance = (maxY - pos[1])*1.4
                        print("distance is " + str(distance))
                        cmds.xform(curveCV, r=1, t=[0, -distance, 0])

            else:
                print(fkControlName+" doesn't exist")

# scale universally first, then replace them with available templates
def adjustControlCurves():
    global allFitJoints
    global footFitJointsGlobal
    global handFitJointsGlobal
    global torsoFitJoints
    global iKSplineFitJointsGlobal
    global headFitJointsGlobal
    global meshesSize
    global deformJointMeshesList

    allControlCurves = []
    # find all curve controls under MotionSystem
    if cmds.objExists("MotionSystem"):
        allControls = cmds.listRelatives("MotionSystem", children=1, ad=1)
        for item in allControls:
            if cmds.nodeType(item) == 'transform':
                print(item)
                itemShapeList = cmds.listRelatives(item, children=1, shapes=1)
                if itemShapeList:
                    if cmds.nodeType(itemShapeList[0]) == 'nurbsCurve':
                        allControlCurves.append(item)

    if allControlCurves:
        universallyScaleControls(allControlCurves)
        adjustPoleVectorControls(allControlCurves)
        adjustBlendIKFKControls(allControlCurves)

    # fix all FK control curves >> not working
    # if allFitJoints:
    #     for fitJoint in allFitJoints:
    #         createFKCircleCurve(fitJoint)

    # IKLeg >> wrong name, need fix. Always: IKLeg_R then IKLegFront_R. More than 2, IKLegFront1_R, IKLegFront2_R, ...
    if footFitJointsGlobal:
        createBoxControls(footFitJointsGlobal)

    # IKArm
    if handFitJointsGlobal:
        createBoxControls(handFitJointsGlobal)

    # IKSpine. >> need fix IKhybrid controls as well
    if torsoFitJoints:
        createBoxControls(torsoFitJoints)

    # create FKHead_M_template
    if headFitJointsGlobal:
        for headFitJoint in headFitJointsGlobal:
            deformJointList = getDeformJointFromFitJoint(headFitJoint)
            side = None
            for deformJoint in deformJointList:
                print(deformJoint)
                if deformJoint.endswith("_R"):
                    side = "_R"
                elif deformJoint.endswith("_L"):
                    side = "_L"
                elif deformJoint.endswith("_M"):
                    side = "_M"

                if len(headFitJointsGlobal) > 1:
                    indexNum = headFitJointsGlobal.index(headFitJoint) + 1
                    fkHeadConTemlateName = "FK" + headFitJoint + str(indexNum) + side + "_template"
                    if cmds.objExists("FK" + headFitJoint + str(indexNum) + side + "_template"):
                        cmds.delete("FK" + headFitJoint + str(indexNum) + side + "_template")

                    fkHeadConName = "FK" + headFitJoint + str(indexNum) + side
                    if cmds.objExists(fkHeadConName):
                        fkHeadConNameSize = maxAllDirectionBBoxMeshes(fkHeadConName)
                        headConTemplate = cmds.circle(name=fkHeadConTemlateName, radius=(fkHeadConNameSize / 2), normal=[0, 0, 1], ch=0)[0]
                        lightblue(headConTemplate)
                        cmds.parent(headConTemplate, "curveTemplates_Grp")

                elif len(headFitJointsGlobal) == 1:
                    fkHeadConTemlateName = "FK" + headFitJoint + side + "_template"
                    if cmds.objExists("FK" + headFitJoint + side + "_template"):
                        cmds.delete("FK" + headFitJoint + side + "_template")

                    fkHeadConName = "FK" + headFitJoint + side
                    if cmds.objExists(fkHeadConName):
                        fkHeadConNameSize = maxAllDirectionBBoxMeshes(fkHeadConName)
                        headConTemplate = cmds.circle(name=fkHeadConTemlateName, radius=(fkHeadConNameSize / 2), normal=[0, 0, 1], ch=0)[0]
                        lightblue(headConTemplate)
                        cmds.parent(headConTemplate, "curveTemplates_Grp")

    # Adjust HipSwinger and create RootX_M_template
    adjustRootControls()

    # main control
    if meshesSize:
        if cmds.objExists("Main_template"):
            cmds.delete("Main_template")
        # use Y (mesh height)
        mainConTemplate = cmds.circle(name="Main_template", radius=(meshesSize[1]/2)*1.5, normal=[0, 1, 0], ch=0)[0]
        cmds.parent(mainConTemplate, "curveTemplates_Grp")

    # manually swap Main
    cmds.select("Main", r=1)
    if cmds.objExists("Main_template"):
        cmds.select("Main_template", add=1)
        mel.eval('asSwapCurve')
        cmds.select(clear=1)

    # start swapping available template controls
    if allControlCurves:
        for controlCurve in allControlCurves:
            if cmds.objExists(controlCurve+"_template"):
                cmds.select(controlCurve, replace=1)
                cmds.select(controlCurve+"_template", add=1)
                mel.eval('asSwapCurve')
                cmds.select(clear=1)


    # move JawFK control out of deform joint mesh BBox in +Z direction
    # move HeadFK control out of deform joint mesh BBox in +Y direction
    # move EyeFK controls (R only, mirror over later) out of deform joint mesh BBox in +Z direction


    if headFitJointsGlobal:
        moveControlOutOfMesh(headFitJointsGlobal)

    global eyeFitJointsGlobal
    if eyeFitJointsGlobal:
        moveControlOutOfMesh(eyeFitJointsGlobal)

    # only find jaw using fitJoint name Jaw*
    jawFitJoints = []
    if allFitJoints:
        for fitJoint in allFitJoints:
            if fitJoint.startswith("Jaw") or fitJoint.startswith("jaw"):
                jawFitJoints.append(fitJoint)
        if jawFitJoints:
            if endJointsList:
                jawFitJoints = filterOutListOfJoints(jawFitJoints, endJointsList)
            moveControlOutOfMesh(jawFitJoints)

        cmds.select(clear=1)
        # mirror from right to left
        mel.eval("asMirrorControlCurves 0 ControlSet")

def smallerControlCurves():
    currentSelection = cmds.ls(sl=1)
    print(currentSelection)
    if currentSelection:
        for item in currentSelection:
            itemShape = cmds.listRelatives(item, children=1, shapes=1)[0]
            print(itemShape)
            if cmds.nodeType(itemShape) == 'nurbsCurve':
                print("scaling smaller")
                scaleControlCVs(item, 0.8, None)
            else:
                print("this one is not curve")
    cmds.select(currentSelection, r=1)

def biggerControlCurves():
    currentSelection = cmds.ls(sl=1)
    print(currentSelection)
    if currentSelection:
        for item in currentSelection:
            itemShape = cmds.listRelatives(item, children=1, shapes=1)[0]
            print(itemShape)
            if cmds.nodeType(itemShape) == 'nurbsCurve':
                print("scaling smaller")
                scaleControlCVs(item, 1.2, None)
            else:
                print("this one is not curve")
    cmds.select(currentSelection, r=1)

def rightToLeftControls():
    mel.eval("asMirrorControlCurves 0 ControlSet")
##################
# Deformed Props #
##################

def autoAttachDeformedProps():
    global deformedProps
    global bindingJointsList
    global originalBodyMeshes

    if deformedProps and originalBodyMeshes and bindingJointsList:
        dupOriginalBodyMeshes = []
        for bodyMesh in originalBodyMeshes:
            dupBodyMesh = cmds.duplicate(bodyMesh)[0]
            cmds.skinCluster(bindingJointsList, dupBodyMesh, sm=0, tsb=1)
            bodyMeshSkin = mel.eval('findRelatedSkinCluster ' + bodyMesh)
            dupBodyMeshSkin = mel.eval('findRelatedSkinCluster ' + dupBodyMesh)
            cmds.copySkinWeights(ss=bodyMeshSkin, ds=dupBodyMeshSkin, nm=True, surfaceAssociation='closestPoint')
            dupOriginalBodyMeshes.append(dupBodyMesh)

        if dupOriginalBodyMeshes:
            mergeddupOriginalBodyMesh = cmds.polyUniteSkinned(dupOriginalBodyMeshes, ch=0)[0]

            mergeddupOriginalBodyMeshSkin = mel.eval('findRelatedSkinCluster ' + mergeddupOriginalBodyMesh)

            for prop in deformedProps:
                cmds.delete(prop, ch=1)
                propSkin = cmds.skinCluster(bindingJointsList, prop, sm=0, tsb=1)[0]
                cmds.copySkinWeights(ss=mergeddupOriginalBodyMeshSkin, ds=propSkin, nm=True, surfaceAssociation='closestPoint')

            cmds.showHidden("deformedProps_Grp")
            cmds.parent(mergeddupOriginalBodyMesh, "TRCR_Grp")
            cmds.hide(mergeddupOriginalBodyMesh)
        else:
            print("Function failed. dupOriginalBodyMeshes doesn't exist")
    else:
        print("Dont have enough variables for auto attach deformed props")
    cmds.select(clear=1)

#######################################
# Attach non-deformed props functions #
#######################################

def createFollicle(vertex, bodyMesh):
    geo = pm.PyNode(bodyMesh)
    uvMap = pm.polyListComponentConversion(vertex, fv=True, tuv=True)
    uvCoord = pm.polyEditUV(uvMap, q=True)

    fol = pm.createNode('transform', ss=True)
    folShape = pm.createNode('follicle', n=fol.name() + 'Shape', p=fol, ss=True)
    pm.setAttr(folShape+".visibility", 0)
    if not pm.objExists("follicleGroup"):
        pm.group(n="follicleGroup", empty=True)
        if pm.objExists("Group"):
            pm.parent("follicleGroup", "Group")
    pm.parent(fol, "follicleGroup")

    pm.connectAttr(geo + '.outMesh', folShape + '.inputMesh')
    pm.connectAttr(geo + '.worldMatrix[0]', folShape + '.inputWorldMatrix')
    pm.connectAttr(folShape + '.outRotate', fol + '.rotate')
    pm.connectAttr(folShape + '.outTranslate', fol + '.translate')
    fol.inheritsTransform.set(False)
    try:
        folShape.parameterU.set(uvCoord[0])
        folShape.parameterV.set(uvCoord[1])
    except:
        print("Your mainBodyMesh has no UV to do autoAttachNonDeformedProps")
        return None
    return str(fol)

def pyRayIntersect(mesh, point, direction=(0.0, 1.0, 0.0)):
    OpenMaya.MGlobal.selectByName(mesh,OpenMaya.MGlobal.kReplaceList)
    sList = OpenMaya.MSelectionList()
    # Assign current selection to the selection list object
    OpenMaya.MGlobal.getActiveSelectionList(sList)
    item = OpenMaya.MDagPath()
    sList.getDagPath(0, item)
    item.extendToShape()
    fnMesh = OpenMaya.MFnMesh(item)
    raySource = OpenMaya.MFloatPoint(point[0], point[1], point[2], 1.0)
    rayDir = OpenMaya.MFloatVector(direction[0], direction[1], direction[2])
    faceIds = None
    triIds = None
    idsSorted = False
    testBothDirections = False
    worldSpace = OpenMaya.MSpace.kWorld
    maxParam = 999999
    accelParams = None
    sortHits = True
    hitPoints = OpenMaya.MFloatPointArray()
    #hitRayParams = OM.MScriptUtil().asFloatPtr()
    hitRayParams = OpenMaya.MFloatArray()
    hitFaces = OpenMaya.MIntArray()
    hitTris = None
    hitBarys1 = None
    hitBarys2 = None
    tolerance = 0.0001
    hit = fnMesh.allIntersections(raySource, rayDir, faceIds, triIds, idsSorted, worldSpace, maxParam, testBothDirections, accelParams, sortHits, hitPoints, hitRayParams, hitFaces, hitTris, hitBarys1, hitBarys2, tolerance)
    result = int(fmod(len(hitFaces), 2))

    #clear selection as may cause problem if the function is called multiple times in succession
    #OM.MGlobal.clearSelectionList()
    return result

def testIntersect(bodyMesh, prop):
    container = bodyMesh
    checkInsideObj = prop
    allVtx = pm.ls(str(checkInsideObj) + '.vtx[*]', fl=1)
    allIn = []
    for eachVtx in allVtx:
        location = pm.pointPosition(eachVtx, w=1)
        test = pyRayIntersect(container, location, (0, 1, 0))
        if (test):
            allIn.append(eachVtx)
    pm.select(allIn)
    return allIn

def getMaxSize(propGeo):
    bBox= cmds.exactWorldBoundingBox(propGeo)
    lengthX = bBox[3]-bBox[0]
    lengthY = bBox[4]-bBox[1]
    lengthZ = bBox[5]-bBox[2]
    maxLength = max(lengthX, lengthY, lengthZ)
    return maxLength

def GetDistance(objA, objB):
    gObjA = cmds.xform(objA, q=True, t=True, ws=True)
    gObjB = cmds.xform(objB, q=True, t=True, ws=True)
    return sqrt(pow(gObjA[0] - gObjB[0], 2) + pow(gObjA[1] - gObjB[1], 2) + pow(gObjA[2] - gObjB[2], 2))

def findClosestVerToCurrentVer(currentVer, mainMesh):
    # find the closest vertex on main mesh to current vertex (on prop)
    pos = []
    pos = cmds.xform(currentVer, q=1, ws=1, t=1)
    cpom = cmds.createNode('closestPointOnMesh')
    shape = cmds.listRelatives(mainMesh, s=True)[0]
    cmds.connectAttr('%s.outMesh' % shape, '%s.inMesh' % cpom)
    cmds.setAttr('%s.inPosition' % cpom, pos[0], pos[1], pos[2], type="double3")

    # vertex index
    vtxIndx = cmds.getAttr(cpom + ".closestVertexIndex")
    closestVer = "{0}.vtx[{1}]".format(mainMesh, vtxIndx)

    # delete node when done calculating
    cmds.delete(cpom)

    return closestVer

def closestVerToSurface(verList, mainMesh):
    minDistance = 9999999999999
    minClosestVer = None
    for ver in verList:
        closestVer = findClosestVerToCurrentVer(ver, mainMesh)
        distance = GetDistance(ver, closestVer)
        if distance <= minDistance:
            minDistance = distance
            minClosestVer = ver

    if not minClosestVer:
        raise Exception("Cannot find the closest vertex")
    return minClosestVer

def attachProp(propList, bodyMesh):
    global mainRigControl
    if cmds.objExists(bodyMesh) and cmds.objExists(mainRigControl):
        for prop in propList:
            if cmds.objExists(prop):
                # find intersecting vertices
                inVerList = testIntersect(bodyMesh, prop)
                if inVerList:
                    # if the prop intersects with body mesh, use intersect vertices' center for pivot of the prop
                    # how to find the closest vertice to the mainBody surface?

                    # centerPos = getCenterOfVertices(selectedVertices)
                    # cmds.xform(prop, pivots=centerPos, ws=True)

                    # this step of selecting inVerList is to avoid Maya crash
                    selectedVertices = cmds.ls(sl=True, flatten=1)
                    closestVerOnMainBody = closestVerToSurface(selectedVertices, bodyMesh)
                    closestVerOnMainBodyPos = cmds.xform(closestVerOnMainBody, q=1, ws=1, t=1)
                    cmds.xform(prop, pivots=closestVerOnMainBodyPos, ws=True)

                else:
                    # center pivot the prop
                    cmds.xform(prop, centerPivots=1)
                    # find closest vertex on body mesh to the prop's center pivot
                    nearestVerOnBodyMesh = getClosestVert(prop, bodyMesh)
                    # create & place a body-locator at this vertex
                    bodyLoc = cmds.spaceLocator(absolute=1, position=cmds.xform(nearestVerOnBodyMesh, q=1, translation=True))[0]
                    # find closest vertex on prop to this body-locator
                    nearestVerOnProp = getClosestVert(bodyLoc, prop)
                    # delete body-locator
                    cmds.delete(bodyLoc)
                    # set prop pivot to the closest vertex on prop
                    cmds.xform(prop, pivots=cmds.xform(nearestVerOnProp, q=1, translation=True), ws=True)

                # find the closest vertex to this pivot
                nearestVertex = getClosestVert(prop, bodyMesh)
                # cmds.select(nearestVertex, r=True)
                # create follicle at this vertex
                if nearestVertex and bodyMesh and cmds.objExists(bodyMesh):
                    folName = createFollicle(nearestVertex, bodyMesh)

                    if folName:
                        # parent constraint the prop to this follicle
                        cmds.parentConstraint(folName, prop, mo=True)
                        cmds.scaleConstraint(mainRigControl, prop)
                        # this one makes the script run slower but visually pleasing
                        # cmds.refresh()

def find_most_influential_jnt(bodySkin, closestVert):
    # queries all joints influencing the current vertex with value above given threshold
    influences = cmds.skinPercent(bodySkin, closestVert, q=True, ignoreBelow=0.2, t=None)
    inf_values_dict = {}
    for systemJnt in influences:
        inf_values_dict[systemJnt] = cmds.skinPercent(bodySkin, closestVert, q=True, t=systemJnt)

    sorted_inf_values = sorted(inf_values_dict.items(), key=lambda x: x[-1], reverse=True)
    # returns a list of tuples of each joint and its influence value
    # sorted by the influence value (key to sort is the result of lambda function: x[-1]: value of each key in dict)
    # get the first item in the list
    most_influential_jnt = sorted_inf_values[0][0] # index 2 times to get the system joint name
    return most_influential_jnt

def createJoints(bodyMesh=None, propList=None):
    # find follicleGroup >> if not exist >> raise error
    if cmds.objExists("follicleGroup"):
        if bodyMesh and cmds.objExists(bodyMesh) and propList:
            # query the main body's skincluster name
            bodySkin = mel.eval('findRelatedSkinCluster ' + bodyMesh)
            if not bodySkin:
                raise Exception("Body skinCluster is not found, you must create skinCluster for body mesh first")

            for prop in propList:
                if cmds.objExists(prop):
                    # list connection of prop, to find who parent constraint them (prop parent) >> if find nothing >> raise error
                    parentConList = cmds.listRelatives(prop, children=True, type='constraint')
                    if parentConList:
                        parentCon = parentConList[0]
                        # get parent: follicle/ control which drive the prop
                        prop_parent = cmds.parentConstraint(parentCon, q=1, targetList=1)
                        # delete the constraints since we wont need it, skincluster will drive the prop
                        cmds.delete(prop, constraints=1)
                        # create joints at prop positions (prop joint
                        cmds.select(clear=True)
                        prop_jnt = cmds.joint(name=prop+"_fol_jnt")
                        # get closest Vertex on Body from prop
                        nearest_ver = getClosestVert(prop, bodyMesh)
                        # find its biggest influence (main joint in the system)
                        main_jnt = find_most_influential_jnt(bodySkin, nearest_ver)
                        # parent prop joint under this main joint
                        cmds.parent(prop_jnt, main_jnt)
                        # parent constraint (propParent, propJnt), with no offset, otherwise props will go crazy
                        cmds.parentConstraint(prop_parent, prop_jnt, mo=False)
                        # scale constraint (Main, propJnt)
                        cmds.scaleConstraint(mainRigControl, prop_jnt, mo=True)
                        # bind skin propJoint to prop
                        cmds.skinCluster(prop_jnt, prop, skinMethod=0, toSelectedBones=1)

# find which original mesh is near them then attach
def autoAttachNonDeformedProps():
    global mainBodyMesh
    global nonDeformedProps
    if mainBodyMesh and cmds.objExists(mainBodyMesh) and nonDeformedProps:
        cmds.showHidden("nonDeformedProps_Grp")
        attachProp(nonDeformedProps, mainBodyMesh)
    else:
        print("MainBodyMesh or nonDeformedProps are not available")
    cmds.select(clear=1)

def createJointsForNonDeformedProps():
    global mainBodyMesh
    global nonDeformedProps
    if mainBodyMesh and cmds.objExists(mainBodyMesh) and nonDeformedProps:
        createJoints(mainBodyMesh, nonDeformedProps)
        cmds.select(clear=1)

def jointsDisplayOff():
    if cmds.objExists("Main"):
        joints = cmds.listRelatives("Main", type="joint", ad=True)
        for j in joints:
            cmds.setAttr(j + ".drawStyle", 2)
        cmds.select(clear=True)

# Hide joints using draw
# bring all original meshes into "Geometry"
# All geometry > layer > "R"
# Deform Joint meshes (have skin cluster) > Proxy layer > "R" and hide
# Delete TRCR
def cleanUpEverything():
    jointsDisplayOff()
    global originalBodyMeshes
    global deformedProps
    global nonDeformedProps

    if originalBodyMeshes and cmds.objExists("Geometry"):
        cmds.parent(originalBodyMeshes, "Geometry")
    if deformedProps and cmds.objExists("Geometry"):
        if not cmds.objExists("deformedProps_Main"):
            cmds.group(name="deformedProps_Main", empty=1)
            cmds.parent("deformedProps_Main", "Geometry")
        cmds.parent(deformedProps, "deformedProps_Main")
    if nonDeformedProps and cmds.objExists("Geometry"):
        if not cmds.objExists("nonDeformedProps_Main"):
            cmds.group(name="nonDeformedProps_Main", empty=1)
            cmds.parent("nonDeformedProps_Main", "Geometry")
        cmds.parent(nonDeformedProps, "nonDeformedProps_Main")

    if cmds.objExists("Geometry"):
        existingLayers = cmds.ls(type="displayLayer")
        geoLayerName = "geo"
        if geoLayerName not in existingLayers:
            geoLayer = cmds.createDisplayLayer("Geometry", name=geoLayerName)
        cmds.setAttr("{}.displayType".format(geoLayerName), 2)  # Change layer to reference.

        cmds.select("Geometry", r=1)
        mel.eval('layerEditorAddObjects {}'.format(geoLayerName))

    if cmds.objExists("TRCR_Grp"):
        cmds.delete("TRCR_Grp")

    cmds.select(clear=1)

#############################################
# additional functions for attach prop tool #
#############################################
def deleteSetup():
    # remove skin history
    for prop in propList:
        propSkin = mel.eval('findRelatedSkinCluster ' + prop)
        if propSkin:
            cmds.skinCluster(prop, unbind=True, edit=True)
    # delete joints
    folJntList = cmds.ls("*_{}".format("fol_jnt"))
    if folJntList:
        cmds.delete(folJntList)
    # delete constraint
    if cmds.objExists("follicleGroup"):
        cmds.delete("follicleGroup")
    cmds.delete(propList, constraints=1)

def setPropList():
    global propList
    propList = cmds.ls(sl=True)
    if not propList:
        raise Exception("Please select some props")
    load_selected_as(propList, propList_tf)

def setMainBody():
    global mainBody
    mainBody = cmds.ls(sl=True)[0]
    if not mainBody:
        raise Exception("Please select the main character body")
    load_selected_as(mainBody, mainBody_tf)

def setMainRigControl():
    global mainRigControl
    mainRigControl = cmds.ls(sl=True)[0]
    if not mainRigControl:
        raise Exception("Please select the main rig control")
    load_selected_as(mainRigControl, mainRigControl_tf)

def checkBoxOn():
    global controlCheck
    controlCheck = True
    return controlCheck

def checkBoxOff():
    global controlCheck
    controlCheck = False
    return controlCheck

def setCustomPivot():
    global customPivotVertexList
    customPivotVertexList = cmds.ls(sl=True, flatten=True)
    load_selected_as(customPivotVertexList, customPivotVertexList_tf)

def create_AttachPropsToolUI(winID):
    window_size = (400, 320)
    cmds.window(winID, e=True, wh=window_size)

    txt_field_width = 370

    main_lo = cmds.columnLayout(p=winID)

    cmds.text("\n Select Props: ")
    set_props_lo = cmds.rowLayout(p=main_lo, nc=2, cw2=(txt_field_width, 25))
    cmds.textField(propList_tf, w=txt_field_width, ed=False)
    set_faces_btn = cmds.button(label=">>", p=set_props_lo, c='setPropList()', width=25)

    cmds.text("\n Select Main Body: ", p=main_lo)
    set_main_body_lo = cmds.rowLayout(p=main_lo, nc=2, cw2=(txt_field_width, 25))
    cmds.textField(mainBody_tf, w=txt_field_width, ed=False)
    set_vertices_btn = cmds.button(label=">>", p=set_main_body_lo, c='setMainBody()', width=25)

    cmds.text("\n Select Main Rig Control (for scale constraint): ", p=main_lo)
    set_main_rig_lo = cmds.rowLayout(p=main_lo, nc=2, cw2=(txt_field_width, 25))
    cmds.textField(mainRigControl_tf, w=txt_field_width, ed=False)
    set_vertices_btn = cmds.button(label=">>", p=set_main_rig_lo, c='setMainRigControl()', width=25)

    cmds.text("\n Optional: select vertex(s) for custom pivot (for single prop case only): ", p=main_lo)
    set_pivot_lo = cmds.rowLayout(p=main_lo, nc=2, cw2=(txt_field_width, 25))
    cmds.textField(customPivotVertexList_tf, w=txt_field_width, ed=False)
    set_vertices_btn = cmds.button(label=">>", p=set_pivot_lo, c='setCustomPivot()', width=25)

    sep1 = cmds.separator(w=window_size[0], h=20, p=main_lo)
    ctrlBox1 = cmds.checkBox(label='Create Prop Controls', value=False, onCommand='checkBoxOn()', offCommand='checkBoxOff()', p=main_lo)

    sep2 = cmds.separator(w=window_size[0], h=20, p=main_lo)

    attach_prop_lo = cmds.rowLayout(p=main_lo, nc=3)
    attach_btn = cmds.button(label="Attach Props", p=attach_prop_lo, c='attachProp(propList, mainBody)', width=130, align="left")
    createJnt_btn = cmds.button(label="Create Joints (for Game)", p=attach_prop_lo, c='createJoints()', width=130, align="left")
    delete_btn = cmds.button(label="Delete Setup", p=attach_prop_lo, c='deleteSetup()', width=130, align="left")

def show_AttachPropsToolUI(winID):
    if cmds.window(winID, exists=True):
        cmds.deleteUI(winID)
    cmds.window(winID)
    create_AttachPropsToolUI(winID)
    cmds.showWindow(winID)
##############################################
# Do it all
def doItAll():
    global originalBodyMeshes
    global mainBodyMesh
    global nonDeformedProps

    if not mainBodyMesh or not cmds.objExists(mainBodyMesh):
        raise Exception('mainBodyMesh is not defined. Please assign it in Input tab')
    placeFitJointIntoPlace()
    # fixPoleVector()
    buildAdvancedSkeleton()
    adjustControlCurves()
    bindDeformJointMeshesToDeformJoints_then_CopySkin()
    # need to have field for user input relax_num. When do it all, relax 2 times
    smoothSkinning(MllInterface, originalBodyMeshes, 2)
    createProxyRig()
    autoAttachDeformedProps()
    autoAttachNonDeformedProps()
    createJoints(mainBodyMesh, nonDeformedProps)
    cleanUpEverything()

######################################
# load mesh variables from selection #
######################################

def load_selected_as(sel, text_field):
    text_field = cmds.textField(text_field, e=True, tx=str(sel))

def chooseMainBodyMesh():
    global mainBodyMesh
    mainBodyMeshSelection = cmds.ls(sl=1)
    if len(mainBodyMeshSelection) > 1:
        raise Exception('Please select 1 mesh only')
    mainBodyMesh = mainBodyMeshSelection[0]
    load_selected_as(mainBodyMesh, mainBodyMeshTF)
    cmds.select(clear=True)

def chooseDeformedProps():
    global deformedProps
    deformedProps = cmds.ls(sl=1)
    if not deformedProps:
        raise Exception("Please select deformed props")
    load_selected_as(deformedProps, deformedPropsTF)
    cmds.select(clear=1)
    print(deformedProps)
    createStructure(None, deformedProps, None, None)

def chooseNonDeformedProps():
    global nonDeformedProps
    global mainBodyMesh
    nonDeformedProps = cmds.ls(sl=1)
    if not nonDeformedProps:
        raise Exception("Please select non-deformed props")
    load_selected_as(nonDeformedProps, nonDeformedPropsTF)
    cmds.select(clear=1)
    print(nonDeformedProps)
    createStructure(None, None, nonDeformedProps, None)

def chooseFaceItems():
    global faceItems
    faceItems = cmds.ls(sl=1)
    if not faceItems:
        raise Exception("Please select face items")
    load_selected_as(faceItems, faceItemsTF)
    for faceItem in faceItems:
        cmds.xform(faceItem, cp=1)
    cmds.select(clear=1)
    print(faceItems)
    createStructure(None, None, None, faceItems)

def chooseOriginalBodyMeshes():
    global faceItems
    global deformedProps
    global nonDeformedProps
    global originalBodyMeshes
    skipList = []
    if faceItems:
        skipList.extend(faceItems)
    if deformedProps:
        skipList.extend(deformedProps)
    if nonDeformedProps:
        skipList.extend(nonDeformedProps)
    if originalBodyMeshes:
        skipList.extend(originalBodyMeshes)

    # no reset originalBodyMeshes?
    currentSelection = cmds.ls(sl=True)
    if not currentSelection:
        raise Exception("Please select original body meshes")
    for mesh in currentSelection:
        print(mesh)
        if skipList:
            if mesh not in skipList:
                cmds.xform(mesh, cp=1)
                originalBodyMeshes.append(mesh)
        else:
            cmds.xform(mesh, cp=1)
            print(originalBodyMeshes)
            originalBodyMeshes.append(mesh)
    load_selected_as(originalBodyMeshes, originalBodyMeshesTF)
    cmds.select(clear=True)
    print(originalBodyMeshes)
    createStructure(originalBodyMeshes, None, None, None)

####################
# Toggle selection #
####################
def toggleFaceSelection():
    currentFaceSelectionStatus = cmds.selectType(q=1, polymesh=1)
    if currentFaceSelectionStatus:
        cmds.selectType(polymesh=0)
    else:
        cmds.selectType(polymesh=1)

def toggleJointSelection():
    currentJointSelectionStatus = cmds.selectType(q=1, joint=1)
    if currentJointSelectionStatus:
        cmds.selectType(joint=0)
    else:
        cmds.selectType(joint=1)

def toggleObject(itemOn, itemOff):
    panelList = cmds.getPanel(type='modelPanel')
    myPanel = cmds.getPanel(wf=True)
    if myPanel not in panelList:
        raise Exception("The current panel is not viewport")
    if (cmds.modelEditor(myPanel, query=True, **itemOn)):
        cmds.modelEditor(myPanel, edit=True, **itemOff)
    else:
        cmds.modelEditor(myPanel, edit=True, **itemOn)

def toggleJointDisplay():
    # toggleObject({'joints': 1}, {'joints': 0})
    if cmds.objExists("Main"):
        joints = cmds.listRelatives("Main", type="joint", ad=True)
        if cmds.getAttr(joints[0] + ".drawStyle") == 0:
            for j in joints:
                cmds.setAttr(j + ".drawStyle", 2)
        else:
            for j in joints:
                cmds.setAttr(j + ".drawStyle", 0)
    elif cmds.objExists("FitSkeleton"):
        joints = cmds.listRelatives("FitSkeleton", type="joint", ad=True)
        if cmds.getAttr(joints[0] + ".drawStyle") == 0:
            for j in joints:
                cmds.setAttr(j + ".drawStyle", 2)
        else:
            for j in joints:
                cmds.setAttr(j + ".drawStyle", 0)

def toggleCutMeshFolderDisplay():
    if cmds.objExists("dupMeshesForCut_Grp"):
        displayStatus = cmds.getAttr("dupMeshesForCut_Grp.visibility")
        if displayStatus:
            cmds.setAttr("dupMeshesForCut_Grp.visibility", 0)
        else:
            cmds.setAttr("dupMeshesForCut_Grp.visibility", 1)
    else:
        print("dupMeshesForCut_Grp doesn't exist")

def toggleFaceDisplay():
    toggleObject({'polymeshes': 1}, {'polymeshes': 0})

def displayFaceItems():
    autoLoadMeshesVariable()
    currentGrpDisplayStatus = cmds.getAttr("faceItems_Grp.visibility")
    if currentGrpDisplayStatus:
        cmds.hide("faceItems_Grp")
    else:
        cmds.showHidden("faceItems_Grp")

def displayDeformJointMeshes_Grp():
    currentGrpDisplayStatus = cmds.getAttr("deformJointMeshes_Grp.visibility")
    if currentGrpDisplayStatus:
        cmds.hide("deformJointMeshes_Grp")
    else:
        cmds.showHidden("deformJointMeshes_Grp")

def autoAdjustJointSize():
    global meshesSize
    if meshesSize:
        cmds.jointDisplayScale(meshesSize[1]/100, a=1)

def manualAdjustJointSize():
    global jointSizeFloatSlider
    jointSize = cmds.floatSlider(jointSizeFloatSlider, q=True, v=True)
    cmds.jointDisplayScale(jointSize, a=1)

######
# UI #
######
import os
import os.path
import glob
import platform

def findAdvancedSkeletonPath():
    global AdvancedSkeletonPath

    scriptPath = os.environ['MAYA_SCRIPT_PATH']
    scriptPathList = scriptPath.split(";")
    print(scriptPath)
    advSkelMel = 'AdvancedSkeleton5.mel'
    # if we need find it first

    advSkelMelPaths = []
    for path in scriptPathList:
        for root, dirs, files in os.walk(r'{}'.format(path)):
            for name in files:
                if name == advSkelMel:
                    advSkelMelPath = os.path.abspath(os.path.join(root, name))
                    advSkelMelPaths.append(advSkelMelPath)

    files = []
    for path in advSkelMelPaths:
        files += glob.glob("{}".format(path))
        # print(files)
    files.sort(key=os.path.getmtime)
    # print("\n".join(files))
    AdvancedSkeletonPath = files[-1]

    # current os
    # currentOs = platform.platform()
    # if currentOs.startswith("Windows"):
    #     print("You're using Windows")

    # / will always work (\ is only for Windows)
    AdvancedSkeletonPath = os.path.normpath(AdvancedSkeletonPath)
    AdvancedSkeletonPath = AdvancedSkeletonPath.replace("\\", "/")
    print(AdvancedSkeletonPath)
    # add Adv Skel path to FitSkeletonShape
    addAdvancedSkeletonPathToFitSkeleton(AdvancedSkeletonPath)
    return AdvancedSkeletonPath

def getAdvancedSkeletonPathFromFitSkeletonShape():
    if cmds.objExists("FitSkeleton"):
        fitSkeletonShape = None
        fitSkeletonShape = cmds.listRelatives("FitSkeleton", children=1, shapes=1)[0]
        print(fitSkeletonShape)

        attrExist = cmds.attributeQuery("AdvancedSkeletonPath", node=fitSkeletonShape, exists=True)
        print(attrExist)
        if attrExist:
            advSkelMelFilePath = cmds.getAttr(fitSkeletonShape+".AdvancedSkeletonPath")
            print(advSkelMelFilePath)
            return advSkelMelFilePath
        else:
            return None

# solve this one. How? Having cycle in thought process
def runAdvancedSkeleton():
    global AdvancedSkeletonPath
    # check if there is source link already in FitSkeleton. If yes, skip looking for the link.
    # return this one to get importFitTemplate >> add advanced skeleton path works
    AdvancedSkeletonPath = getAdvancedSkeletonPathFromFitSkeletonShape()

    if AdvancedSkeletonPath:
        try:
            mel.eval('source "{}";'.format(AdvancedSkeletonPath))
        except:
            cmds.deleteAttr("FitSkeletonShape", at="AdvancedSkeletonPath")
            print("AdvancedSkeletonPath in FitSkeletonShape is not correct. Path is now deleted. Please run again")

    else:
        print("Cannot find Advanced Skeleton link. Searching now.")
        AdvancedSkeletonPath = findAdvancedSkeletonPath()
        print(AdvancedSkeletonPath)

        try:
            mel.eval('source "{}";'.format(AdvancedSkeletonPath))
        except:
            print("Cannot source Advanced Skeleton. Please click on Advanced Skeleton icon to run it")


# user might be required to run Advanced Skeleton first >> or save the script to Advanced Skeleton folder >> get path
def show_UI(winID):
    if cmds.window(winID, exists=True):
        cmds.deleteUI(winID)
    cmds.window(winID)
    create_UI(winID)
    cmds.showWindow(winID)

def getFitSkeletonMenuItems():
    global fitSkeletonsDir
    try:
        runAdvancedSkeleton()
    except:
        print("Cannot search and run Advanced Skeleton. Try to run asGetScriptLocation anyway")
    try:
        fitSkeletonsDir = str(mel.eval("asGetScriptLocation;")) + "/AdvancedSkeleton5Files/fitSkeletons/"
    except:
        raise Exception("Advanced Skeleton is not loaded to run asGetScriptLocation. Please run Advanced Skeleton manually and try again")

    print(fitSkeletonsDir)
    fitFiles = [f for f in listdir(fitSkeletonsDir) if isfile(join(fitSkeletonsDir, f))]
    print(fitFiles)
    return fitFiles

def getLimbMenuItems():
    global limbDir
    try:
        limbDir = str(mel.eval("asGetScriptLocation;"))+"/AdvancedSkeleton5Files/fitSkeletonsLimbs/"
        print(limbDir)
    except:
        raise Exception("Advanced Skeleton is not loaded to get limb directory")
    limbFiles = [f for f in listdir(limbDir) if isfile(join(limbDir, f))]
    print(limbFiles)
    return limbFiles

# need function to create locator at joint >> answer where is the joint in the system
def create_UI(winID):
    global torsoFitJoints
    global legFitJointsGlobal
    global toesIndividualFitJointsGlobal
    global armFitJointsGlobal
    global fingersFitJointsGlobal
    global iKSplineFitJointsGlobal
    global faceItemsFitJointsGlobal
    global masterTabs
    global toolWindowWidth
    global mainBodyMesh
    global jointSizeFloatSlider

    toolWindowWidth = 500

    # Make a new window
    window = cmds.window(winID, e=True, width=toolWindowWidth, title="TRCR-Truong Concept Rig")

    # 1.0
    columnMain = cmds.columnLayout()  # the cyan rectangle

    # 1.1 : First WIDGET: Title
    mainLayout = cmds.rowLayout(numberOfColumns=1, p=columnMain)
    cmds.text(label='\n TRUONG CONCEPT RIG \n', p=mainLayout, width=toolWindowWidth, font="boldLabelFont")
    cmds.text(label='gumroad.com/TruongCgArtist\n', p=columnMain, width=toolWindowWidth)

    sep2 = cmds.separator(w=toolWindowWidth, h=10, p=columnMain)
    selectionTypeNotiRow = cmds.rowLayout(numberOfColumns=4, p=columnMain)
    cmds.text(label="Face Selection", p=selectionTypeNotiRow, width=toolWindowWidth/4)
    cmds.text(label="Face Display", p=selectionTypeNotiRow, width=toolWindowWidth / 4)
    cmds.text(label="Joint Selection", p=selectionTypeNotiRow, width=toolWindowWidth / 4)
    cmds.text(label="Joint Display", p=selectionTypeNotiRow, width=toolWindowWidth / 4)
    # 1.2.2
    selectionTypeRow = cmds.rowLayout(numberOfColumns=4, p=columnMain)
    cmds.iconTextButton(label="Toggle Face Selection", p=selectionTypeRow, width=toolWindowWidth/4, i='polyMesh.png', command='toggleFaceSelection()')
    cmds.iconTextButton(label="Toggle Face Display", p=selectionTypeRow, width=toolWindowWidth / 4, i='polyCleanup.png', command='toggleFaceDisplay()')
    cmds.iconTextButton(label="Toggle Joint Selection", p=selectionTypeRow, width=toolWindowWidth/4, i='kinJoint.png', command='toggleJointSelection()')
    cmds.iconTextButton(label="Toggle Joint Display", p=selectionTypeRow, width=toolWindowWidth/4, i='kinRemove.png', command='toggleJointDisplay()')

    cmds.separator(w=toolWindowWidth, h=10, p=columnMain)
    jointSizeRow = cmds.rowLayout(numberOfColumns=4, p=columnMain)
    cmds.text(label=" ", p=jointSizeRow, width=toolWindowWidth/4)
    cmds.text(label=" ", p=jointSizeRow, width=toolWindowWidth / 4)
    cmds.text(label="Joint Size: ", p=jointSizeRow, width=toolWindowWidth / 6)
    jointSizeFloatSlider = cmds.floatSlider(min=0.01, max=10, value=2, step=0.01, width=toolWindowWidth/3, dc='manualAdjustJointSize()')

    cmds.separator(w=toolWindowWidth, h=10, p=columnMain)
    cmds.separator(h=20, p=columnMain)

    # 1.2 : Second WIDGET : tab widget
    form = cmds.formLayout(p=columnMain)
    masterTabs = cmds.tabLayout(width=toolWindowWidth, height=550, scrollable=1, innerMarginWidth=5, innerMarginHeight=5, p=form)

    #####################################
    # 1.2.1 : first tab widget
    inputTab = cmds.columnLayout(p=masterTabs)

    autoLoadMeshesVariable()

    # cmds.text(label='\n Manually define Advanced Skeleton folder path (optional):\n', p=inputTab, width=toolWindowWidth, align='left')
    # advSkelPathRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    # tf_AdvancedSkeletonPath = cmds.textField(AdvancedSkeletonPathTF, w=toolWindowWidth*0.7, h=20, p=advSkelPathRow, ed=1)
    # cmds.button(label='Submit Path', width=toolWindowWidth * 0.3, align='right', p=advSkelPathRow, command='userDefinedAdvancedSkeletonPath(AdvancedSkeletonPathTF)')

    loadFaceItemsRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    tf_faceItems = cmds.textField(faceItemsTF, w=toolWindowWidth*0.7, h=20, p=loadFaceItemsRow, ed=0)
    if faceItems:
        cmds.textField(tf_faceItems, e=True, tx=str(faceItems))
    cmds.button(label='Face Items', width=toolWindowWidth*0.3, align='right', p=loadFaceItemsRow, command='chooseFaceItems()')

    loadDeformedMeshesRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    tf_deformedProps = cmds.textField(deformedPropsTF, w=toolWindowWidth*0.7, h=20, p=loadDeformedMeshesRow, ed=0)
    if deformedProps:
        cmds.textField(tf_deformedProps, e=True, tx=str(deformedProps))
    cmds.button(label='Deformed Props', width=toolWindowWidth*0.3, align='right', p=loadDeformedMeshesRow, command='chooseDeformedProps()')

    loadNonDeformedMeshesRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    tf_nonDeformedProps = cmds.textField(nonDeformedPropsTF, w=toolWindowWidth*0.7, h=20, p=loadNonDeformedMeshesRow, ed=0)
    if nonDeformedProps:
        cmds.textField(tf_nonDeformedProps, e=True, tx=str(nonDeformedProps))
    cmds.button(label='Non-deformed Props', width=toolWindowWidth*0.3, align='right', p=loadNonDeformedMeshesRow, command='chooseNonDeformedProps()')

    loadMainBodyMeshRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    tf_mainBodyMesh = cmds.textField(mainBodyMeshTF, w=toolWindowWidth*0.7, h=20, p=loadMainBodyMeshRow, ed=0)
    cmds.button(label='Main Body Mesh *', width=toolWindowWidth * 0.3, align='right', p=loadMainBodyMeshRow, command='chooseMainBodyMesh()')
    cmds.text(' * Optional. For auto attach props later', p=inputTab, w=toolWindowWidth, align='left')

    loadBodyMeshesRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    tf_bodyMeshes = cmds.textField(originalBodyMeshesTF, w=toolWindowWidth*0.7, h=20, p=loadBodyMeshesRow, ed=0)
    if originalBodyMeshes:
        cmds.textField(tf_bodyMeshes, e=True, tx=str(originalBodyMeshes))
    cmds.button(label='All Body Meshes', width=toolWindowWidth*0.3, align='right', p=loadBodyMeshesRow, command='chooseOriginalBodyMeshes()')

    sep1 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)

    # 1.2.1.2: pick preset, import, update
    global fitFileOptionMenu

    templateRow = cmds.rowLayout(numberOfColumns=3, p=inputTab)
    fitFileOptionMenu = cmds.optionMenu(p=templateRow, width=toolWindowWidth/3)
    fitFiles = getFitSkeletonMenuItems()
    for fitFile in fitFiles:
        cmds.menuItem(label=fitFile, p=fitFileOptionMenu)
    cmds.button(label="Import Fit Skeleton", p=templateRow, width=toolWindowWidth/3, command='importFitTemplate()')
    cmds.button(label="Update Fit Skeleton", p=templateRow, width=toolWindowWidth/3, command='updateFitTemplate()')

    sep11 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)
    sep12 = cmds.separator(h=10, p=inputTab)
    sep21 = cmds.separator(w=toolWindowWidth, h=5, p=inputTab)

    # import extra limbs
    global fitExtraLimbOptionMenu

    limbRow = cmds.rowLayout(numberOfColumns=3, p=inputTab)

    cmds.text(" Select parent joint then: ", p=limbRow, width=toolWindowWidth / 3)

    fitExtraLimbOptionMenu = cmds.optionMenu(p=limbRow, width=toolWindowWidth / 3)
    limbFiles = getLimbMenuItems()
    for limb in limbFiles:
        cmds.menuItem(label=limb, p=fitExtraLimbOptionMenu)

    cmds.button(label="Import Extra Limb", p=limbRow, width=toolWindowWidth/3, command='importExtraLimb()')

    sep12 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)
    sep22 = cmds.separator(h=5, p=inputTab)
    sep23 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)

    global labels
    global iKLabelOptionMenu
    iKLabelRow = cmds.rowLayout(numberOfColumns=4, p=inputTab)
    cmds.text("IK-Label:", p=iKLabelRow, width=toolWindowWidth/4)
    iKLabelOptionMenu = cmds.optionMenu(p=iKLabelRow, width=toolWindowWidth / 4)
    for label in labels:
        cmds.menuItem(label=label, p = iKLabelOptionMenu)
    cmds.button(label="Add", p=iKLabelRow, width=toolWindowWidth/4, command='addIKLabel()')
    cmds.button(label="Remove", p=iKLabelRow, width=toolWindowWidth/4, command='removeIKLabel()')

    sep24 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)
    sep22 = cmds.separator(h=5, p=inputTab)
    sep23 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)

    global attributes
    global attrOptionMenu
    attrRow = cmds.rowLayout(numberOfColumns=4, p=inputTab)
    cmds.text("Attribute:", p=attrRow, width=toolWindowWidth/4)
    attrOptionMenu = cmds.optionMenu(p=attrRow, width=toolWindowWidth/4)
    for attribute in attributes:
        cmds.menuItem(label=attribute, p = attrOptionMenu)
    cmds.button(label="Add", p=attrRow, width=toolWindowWidth/4, command='addAttribute()')
    cmds.button(label="Remove", p=attrRow, width=toolWindowWidth/4, command='removeAttribute()')

    sep25 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)
    sep26 = cmds.separator(h=5, p=inputTab)
    sep27 = cmds.separator(w=toolWindowWidth, h=10, p=inputTab)

    toggleCutMeshRow = cmds.rowLayout(numberOfColumns=2, p=inputTab)
    cmds.text(" Toggle CutMesh & start cutting / import already-Cut Meshes", p=toggleCutMeshRow, width=toolWindowWidth *2/3)
    cmds.button(label="Toggle Cut Mesh", p=toggleCutMeshRow, width=toolWindowWidth / 3, command='toggleCutMeshFolderDisplay()')

    # 1.2.3 : end tab
    cmds.tabLayout(masterTabs, edit=True, tabLabel=((inputTab, 'Input')))

show_UI(trsUI_ID)