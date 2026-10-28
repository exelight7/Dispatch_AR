using UnrealBuildTool;

public class RevealTestTarget : TargetRules
{
	public RevealTestTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("RevealTest");
	}
}
