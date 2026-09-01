Output demo/tokakv-quickstart.gif
Output demo/tokakv-quickstart.webm

Require toka

Set Shell "zsh"
Set Width 1200
Set Height 760
Set FontSize 24
Set TypingSpeed 28ms
Set PlaybackSpeed 1
Set Framerate 30
Set Padding 28

Hide
Type "mkdir -p demo/.quickstart-work && cd demo/.quickstart-work"
Enter
Sleep 500ms
Type "clear"
Enter
Sleep 500ms
Show

Type "toka --version"
Enter
Sleep 1s

Type "toka new tokakv-tour"
Enter
Sleep 1s

Type "cd tokakv-tour && toka add tokakv"
Enter
Sleep 7s

Hide
Type "cp ../../../examples/ten-minute-tour/src/main.tk src/main.tk"
Enter
Sleep 500ms
Type "toka build >build.stdout 2>build.stderr"
Enter
Sleep 18s
Type "clear"
Enter
Sleep 1s
Show

Type "toka run 2>rc10-build-warnings.log"
Enter
Sleep 6s

Type "toka run 2>rc10-build-warnings.log"
Enter
Sleep 6s
