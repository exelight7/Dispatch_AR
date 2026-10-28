#!/bin/sh
# Build the harness and run the gate test. UE ISOLATED TEST - NOT DISPATCH.
# usage: sh run_gates.sh [TestName] [extra editor args]   (default RevealGate.All)
UE=${UE:-D:/EPIC/UE_5.8}
P=$(cd "$(dirname "$0")" && pwd -W)
T=${1:-RevealGate.All}; [ $# -gt 0 ] && shift
cmd //c "$UE\Engine\Build\BatchFiles\Build.bat RevealTestEditor Win64 Development -Project=$P\RevealTest.uproject -WaitMutex -NoHotReload" > "$P/Saved/build.log" 2>&1 || { grep -E "error|Result" "$P/Saved/build.log"; exit 1; }
[ "$T" = RevealGate.All ] && rm -rf "$P/Content/ArabicReveal"
[ "$T" = RevealGate.Tint ] && rm -rf "$P/Content/ArabicRevealTint"
[ "$T" = RevealGate.TintB ] && rm -rf "$P/Content/ArabicRevealTintB"
"$UE/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "$P/RevealTest.uproject" -ExecCmds="Automation RunTests $T;Quit" -unattended -nopause -nosplash -nosound -log -stdout -FullStdOutLogOutput "$@" > "$P/Saved/run_$T.log" 2>&1
grep -E "Test Completed|compile:|Error: |REVEALGATE" "$P/Saved/run_$T.log" | grep -v "UnifiedErrorTest\|LogConfig" | head -40
