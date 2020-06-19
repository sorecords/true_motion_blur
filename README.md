# TRUE MOTION BLUR
Free subframes-based motion blur add-on
for BLENDER 2.8 EEVEE and WORKBENCH render engines

For each scene frame calculates and renders several subframes based on add-on's settings
and blends them together to a final frame.

- Affects camera movements, objects, particles, mesh-simulations like cloth and softbody,
  animated textures, volumetric, semi-transparent and refractive materials.
- Doesn't affect image-, Open VDB- and other sequences which are represented as sequences
  of independent frames

# !!!WARNING!!!
Add-on creates and DELETES temporary nodes, files and folders.
Be careful:
  - If you have folders named "\_True_Motion_Blur_tmp" or "TMB Output"
    in your project or render directory
    they will be completely DELETED from your computer, including all their subfolders and files in them!
  - If you have Image or Alpha Over nodes in your Compositor with
    name starting with "TMB" (e.g. "TMB_Mix") they will be also deleted!

# Install
1. Download zip-archive from github, don't unpack it!
2. Open Blender. From top menu go to -> Edit -> Preferences -> Add-ons -> Install
3. Find downloaded zip-archive and click "Install Add-on" button
4. After add-on installed check enabling checkbox near its name
5. Also enable it in Render Preferences tab

# Uninstall
1. Open Blender. From top menu go to -> Edit -> Preferences -> Add-ons
2. Start to type in "True Motion Blur" until it is shown
3. If you want to temporary disable it for all your projects uncheck enabling checkbox
4. If you want to completely remove it from your computer press the small arrow near its name
  and press "Remove" button
  
# Controls
Add-on replaces native render operator's shortcuts and buttons. Use all the same familiar commands
to start render.
  - Top menu -> Render Image (or `F12` on the keyboard)
  - Top menu -> Render Animation (or `Ctrl`(/`Cmnd` on mac) + `F12` )
  
# Settings
- *Position*:
    Offset for the shutter's time interval, allows to change motion blur trails
- *Shutter*:
    Time taken in frames between shutter open and close. Soft limit is 1, no maximum limit 
- *Samples*:
    Number of subframes to be rendered per frame. More subframes - more smooth blur, but more render time.
- *Quality Boost*:
    Increases render samples for each subframe from its normal amount (lowered versus original scene render samplesamount) up to scene original render samples.Render time increases proportionally
- *Render Passes*:
    - When unchecked subframes are rendered only for those Render Layers outputs which links lead to Composite or File Outputs nodes.
    - When checked renders subframes for all outputs of all Render Layers whose scenes has enabled True motion Blur.
  
# What add-on actually does
- If there isn't any Compositor node tree in the scene yet, it opens Compositor (this is also necessary
to display render results properly), turns on "Use nodes" and "Backdrop" buttons
- If there are nodes in Compositor add-on collect all enabled Render Layers outputs whose links
lead to Composite or File Outputs nodes
- For each active links add-on creates:
    - creates generated Blender Image node to store render results to
    - creates Alpha Over node to switch between Image and original Render Layers output
    - creates File Output node to store temporary images into temporary folder while render subframes
- Than add-on:
    - deletes user Viewer node (don't worry it will be restored in the end) and creates its own
    - calculates number and position of subframes on the timeline based on add-on's "Position", "Shutter" and "Samples" settings
    - decreases scene's sample rate proportionally to subframes number and add-on's "Quality Boost" parameter
    - renders subframes for all Render Layers whose scenes has add-on enabled
    - mixes all prerendered subframes to the final results
    - replaces previously generated images' pixels with those results
    - changes mix-factor of all add-on's Alpha Over mix nodes to 1 to use mixed results
    - if there are scenes in Compositor without enabled add-on including Cycles scenes
      renders them together with subframes mix results
    - if not renders just mixed results
    - if Render Animation was launched saves the frame
- Clean up:
    - unmute all temporary muted nodes
    - deletes all temporary created nodes except images with the latest mixed results and Alpha Over mix nodes
    - deletes all temporary files and folders from disc



