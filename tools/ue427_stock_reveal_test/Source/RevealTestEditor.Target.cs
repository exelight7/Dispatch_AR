using UnrealBuildTool;

public class RevealTestEditorTarget : TargetRules
{
	public RevealTestEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("RevealTest");
	}
}
