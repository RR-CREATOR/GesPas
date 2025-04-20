# GesPas

Its a python app which helps you save and manage your passwords using hand gestures.

To use, open the app, save a password with a unique name, and record a series of gestures using your fingers or hands. Then, to view your password later, just perform those same gestures again — no typing needed.

This runs locally on your device using your camera, with gesture tracking powered by OpenCV and MediaPipe.

First, download the files, create a virtual environment and install the requirements through command:

pip install -r requirements.txt

Then run it using:

python main.py


Once the app opens:

Enter a name and password, and click "Add Password"
You’ll now be taken to the gesture setup page
Set the time between gesture recordings (default is 3 seconds) (PS: Remember to click the set button beside the input box or else it wont apply)

Click "Start", then perform your first gesture, then wait till timer ends for it to be saved
Also if you don't want to press start and stop, just bring your hands in frame to start recording and take them out to stop.

After all gestures are done, click "Done" to finish

You can preview your gestures by clicking "Preview", or view the saved password later by selecting the name from the home page and performing the same gestures again.

You can also delete saved passwords anytime using the 🗑️ button.

Make sure to keep your hand steady during gestures
Try using distinct and repeatable hand shapes or positions
You can use one or both hands
If matching fails, try redoing the gestures the same way as saved
You can preview gestures during setup to check them

Sometimes MediaPipe takes a few seconds to fully load, especially on startup. If it's not detecting your fingers right away, give it a minute, move your hand closer or farther from the camera, or try restarting the app. It usually stabilizes after that.

Once you get past the first few tries, gesture recognition works quite smoothly. It's fast, secure, and a fun way to lock your data using just your hands.
With this, you will no longer need to use google keys or remember complex passwords. Just fun hand gestures
A fun application of computer vision : p

(Credits for idea: karthik)