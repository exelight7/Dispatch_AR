using System.Text.Json.Nodes;
using UAssetAPI;
using UAssetAPI.ExportTypes;

static partial class ArabicStage1
{
    const string RevealName = "WBP_SubtitleBlock_AR_REVEAL_PARTIAL";
    static readonly string[] RevealFunctions = { "Arabic Finish", "Arabic Step", "Arabic Advance Budget", "Arabic Advance Clocks", "Arabic Cancel", "Arabic Skip", "AR Is Combining Code", "AR Timing Characters", "Build Arabic Timing", "Arabic Apply Style", "Arabic Apply Wrap", "Arabic Begin Reveal" };
    static readonly string[] RevealStates = { "ArabicFinished", "ArabicSchedulerArmed", "ArabicCurrentUnit", "ArabicGeneration", "ArabicElapsed", "ArabicUnitDelays" };
    static string RevealPath(string dir) => Path.Combine(dir, RevealName+".uasset");
    static JsonObject ArrayClearR() => X("SetArray",("AssigningProperty",Var2(22,"ArabicUnitDelays",true)),("ArrayInnerProp",null),("Elements",new JsonArray()));
    static bool IsOpR(JsonNode n,string type) => Str(n["$type"]).Contains(".EX_"+type+",");
    static bool IsAssignmentR(JsonNode n,string name) => Str(n["VariableExpression"]?["Variable"]?["New"]?["Path"]?[0])==name || Str(n["Variable"]?["Variable"]?["New"]?["Path"]?[0])==name;
    static JsonObject StateR(string n) => Var2(22,n,true);

    static Build2Context GenerateReveal(JsonObject baseline,string root) {
        foreach(string table in Tables){
            var tableModel=Model(Read(Path.Combine(root,"builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal",table+".uasset")));
            var rows=Arr(Arr(tableModel,"Exports")[0]!["Table"]!,"Data");
            foreach(var row in rows){
                Require(float.Parse(Str(Child(row!,"PrintLetterInterval")["Value"]),System.Globalization.CultureInfo.InvariantCulture)==0.025f,"timing interval changed");
                Require(!Child(row!,"UseAdvancedPrintIntervals")["Value"]!.GetValue<bool>(),"advanced timing requires a separate policy");
            }
        }
        var c=new Build2Context(baseline);var a=c.Asset;var exports=Arr(a,"Exports");
        foreach(string h in Helpers2)c.Functions[h]=Index(a,h);
        foreach(string h in RevealFunctions){int i=exports.Count+1;var e=Copy(Export(a,"Stop Displaying Line"));e["ObjectName"]=h;exports.Add(e);Arr(a,"DependsMap").Add(new JsonArray());c.Functions[h]=i;}
        c.State("Bool","ArabicFinished",JsonValue.Create(false)!);c.State("Bool","ArabicSchedulerArmed",JsonValue.Create(false)!);
        c.State("Int","ArabicCurrentUnit",V(-1));c.State("Int","ArabicGeneration",V(0));c.State("Float","ArabicElapsed",JsonValue.Create(0f)!);
        var array=c.Field("Str","ArabicUnitDelays","CPF_BlueprintVisible, CPF_Transient");array["$type"]="UAssetAPI.FieldTypes.FArrayProperty, UAssetAPI";array["SerializedType"]="ArrayProperty";array["ElementSize"]=16;array["Inner"]=c.Field("Float","ArabicUnitDelays");
        Arr(Export(a,"WBP_SubtitleBlock_C"),"LoadedProperties").Add(array);
        var value=P("Array","ArabicUnitDelays",new JsonArray());value["ArrayType"]="FloatProperty";Set(Export(a,"Default__WBP_SubtitleBlock_C"),value);
        GenerateTimingR(c,baseline,root);GenerateControlR(c,baseline);GenerateStyleR(c,baseline);ExtendEntriesR(c,baseline,root);
        var cls=Export(a,"WBP_SubtitleBlock_C");foreach(string h in RevealFunctions){Arr(cls,"FuncMap").Add(new JsonArray(h,c.Functions[h]));Arr(cls,"Children").Add(c.Functions[h]);AddDep(cls,DepKeys[1],c.Functions[h]);}
        foreach(var p in c.Plans)Arr(a,"Exports")[p.ExportIndex-1]!["ScriptBytecode"]=new JsonArray(p.Cells.Select(x=>(JsonNode)x.Code).ToArray());
        Names(a);Assemble2(c,baseline);
        foreach(var p in c.Plans){var e=Arr(a,"Exports")[p.ExportIndex-1]!;foreach(int r in ScriptReferences2(e["ScriptBytecode"]).Concat(References(e["LoadedProperties"])).Where(x=>x!=0&&x!=22&&x!=p.ExportIndex).Distinct())AddDep(e,DepKeys[1],r);}
        Names(a);return c;
    }

    static void GenerateTimingR(Build2Context c,JsonObject baseline,string root) {
        var p=c.Function("AR Is Combining Code","Bool",("Int","Code"));int f=p.ExportIndex;
        var ranges=Arr(JsonNode.Parse(File.ReadAllText(Path.Combine(root,"tools/asset_inspector/reveal_combining_ranges.json")))!,"ranges");
        foreach(var range in ranges){string next="range_"+p.Cells.Count;p.Jump(next,c.And(c.C("KismetMathLibrary","GreaterEqual_IntInt",Var2(f,"Code"),IC(Num(range![0]))),c.C("KismetMathLibrary","LessEqual_IntInt",Var2(f,"Code"),IC(Num(range[1])))));p.Emit(Return2(BC(true)));p.Mark(next);}
        p.Emit(Return2(BC(false)));p.Emit(X("EndOfScript"));
        p=c.Function("AR Timing Characters","Int",("Str","Input"));f=p.ExportIndex;
        foreach(string n in new[]{"Cursor","Code","Low","Count","Length"})c.Local(f,"Int",n);
        JsonObject L(string n)=>Var2(f,n);void A(string n,JsonObject x)=>p.Emit(Assign2(f,n,x,"Int"));
        A("Cursor",IC(0));A("Count",IC(0));A("Length",c.C("KismetStringLibrary","Len",L("Input")));
        p.Mark("loop");p.Jump("done",c.Less(L("Cursor"),L("Length")));A("Code",c.C("KismetStringLibrary","GetCharacterAsNumber",L("Input"),L("Cursor")));A("Cursor",c.Add(L("Cursor"),1));
        p.Jump("code_ready",c.And(c.C("KismetMathLibrary","GreaterEqual_IntInt",L("Code"),IC(0xD800)),c.C("KismetMathLibrary","LessEqual_IntInt",L("Code"),IC(0xDBFF))));p.Jump("code_ready",c.Less(L("Cursor"),L("Length")));
        A("Low",c.C("KismetStringLibrary","GetCharacterAsNumber",L("Input"),L("Cursor")));
        p.Jump("code_ready",c.And(c.C("KismetMathLibrary","GreaterEqual_IntInt",L("Low"),IC(0xDC00)),c.C("KismetMathLibrary","LessEqual_IntInt",L("Low"),IC(0xDFFF))));
        A("Code",c.C("KismetMathLibrary","Add_IntInt",c.C("KismetMathLibrary","Multiply_IntInt",c.C("KismetMathLibrary","Subtract_IntInt",L("Code"),IC(0xD800)),IC(1024)),c.C("KismetMathLibrary","Add_IntInt",c.C("KismetMathLibrary","Subtract_IntInt",L("Low"),IC(0xDC00)),IC(0x10000))));A("Cursor",c.Add(L("Cursor"),1));
        p.Mark("code_ready");p.Jump("next",c.Not(Call2(c.Functions["AR Is Combining Code"],L("Code"))));
        JsonObject separator=c.IntEq(L("Code"),IC(32));foreach(int code in new[]{9,10,13})separator=c.Or(separator,c.IntEq(L("Code"),IC(code)));
        p.Jump("next",c.Not(separator));A("Count",c.Add(L("Count"),1));p.Mark("next");p.Jump("loop");p.Mark("done");p.Emit(Return2(L("Count")));p.Emit(X("EndOfScript"));

        // Clone the frozen segmentation helper and instrument its two unit-flush sites. The original helper stays identical.
        // The clone keeps the FString return; it is bare-called at Set Displayed Line (Run 2 crash). Round 019 RepairTiming019 makes it void.
        int timing=c.Functions["Build Arabic Timing"];var source=Export(baseline,"Build Arabic Markup");var e=Copy(source);e["ObjectName"]="Build Arabic Timing";Arr(c.Asset,"Exports")[timing-1]=e;
        Rebind2(e["ScriptBytecode"],Index(baseline,"Build Arabic Markup"),timing,n=>n);
        c.Local(timing,"Float","UnitDelay");c.Local(timing,"Int","DiscardedArrayIndex");
        var script=Arr(source,"ScriptBytecode");p=new Asm2{ExportIndex=timing,SourceExportIndex=Index(baseline,"Build Arabic Markup"),Original=script.DeepClone().AsArray()};c.Plans.Add(p);p.Emit(ArrayClearR());
        JsonObject T(string n)=>Var2(timing,n);
        for(int i=0;i<script.Count;i++) {
            bool flush=false;JsonWalk2(script[i],"$",(n,_)=>{if(n["StackNode"] is JsonValue && Num(n["StackNode"])==c.Functions["AR Escape"])flush=true;});
            if(flush){p.Mark("old_"+i);p.Emit(Assign2(timing,"UnitDelay",FC(0),"Float"));
                p.Jump("store_"+i,c.Not(c.Or(c.IntEq(T("Phase"),IC(0)),c.Less(c.C("KismetMathLibrary","Subtract_IntInt",T("Count"),IC(1)),T("SpeakerCount")))));
                p.Emit(Assign2(timing,"UnitDelay",c.C("KismetMathLibrary","Multiply_FloatFloat",c.C("KismetMathLibrary","Conv_IntToFloat",Call2(c.Functions["AR Timing Characters"],T("Pending"))),FC(0.025f)),"Float"));
                p.Mark("store_"+i);p.Emit(Assign2(timing,"DiscardedArrayIndex",c.C("KismetArrayLibrary","Array_Add",StateR("ArabicUnitDelays"),T("UnitDelay")),"Int"));
            }
            p.Old(i);if(flush)p.Cells[^1].Label="flushed_original_"+i;
            Rebind2(p.Cells[^1].Code,Index(baseline,"Build Arabic Markup"),timing,n=>n);
        }
    }

    static void GenerateControlR(Build2Context c,JsonObject baseline) {
        var p=c.Function("Arabic Finish",null,("Bool","StoppedEarly"));int f=p.ExportIndex;
        p.Jump("return",c.And(StateR("bArabicActive"),c.Not(StateR("ArabicFinished"))));
        p.Emit(Assign2(22,"ArabicFinished",BC(true),"Bool",true));p.Emit(Assign2(22,"ArabicSchedulerArmed",BC(false),"Bool",true));p.Emit(Assign2(22,"bArabicActive",BC(false),"Bool",true));
        p.Emit(Assign2(22,"ArabicCurrentUnit",c.C("KismetMathLibrary","Subtract_IntInt",StateR("ArabicUnitCount"),IC(1)),"Int",true));p.Emit(Call2(c.Functions[Helpers2[5]],StateR("ArabicCurrentUnit")));
        var broadcast=Copy(Arr(Export(baseline,"ExecuteUbergraph_WBP_SubtitleBlock"),"ScriptBytecode")[41]!);broadcast["Parameters"]=new JsonArray(Var2(f,"StoppedEarly"));p.Emit(broadcast);
        p.Mark("return");p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Skip",null);p.Emit(Call2(c.Functions["Arabic Finish"],BC(true)));p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Cancel",null);
        p.Emit(Assign2(22,"ArabicSchedulerArmed",BC(false),"Bool",true));p.Emit(Assign2(22,"bArabicActive",BC(false),"Bool",true));p.Emit(Assign2(22,"ArabicFinished",BC(false),"Bool",true));
        p.Emit(Assign2(22,"ArabicGeneration",c.Add(StateR("ArabicGeneration"),1),"Int",true));
        foreach(string n in new[]{"ArabicCurrentUnit","ArabicUnitCount","ArabicSpeakerUnits"})p.Emit(Assign2(22,n,IC(n=="ArabicCurrentUnit"?-1:0),"Int",true));
        p.Emit(Assign2(22,"ArabicElapsed",FC(0),"Float",true));p.Emit(ArrayClearR());p.Emit(Call2(c.Functions[Helpers2[5]],IC(-1)));foreach(string w in Widgets)p.Emit(Visible2(w,1));p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Step",null);
        p.Jump("return",c.And(c.And(StateR("bArabicActive"),StateR("ArabicSchedulerArmed")),c.Not(StateR("ArabicFinished"))));
        p.Jump("finish",c.Less(StateR("ArabicCurrentUnit"),c.C("KismetMathLibrary","Subtract_IntInt",StateR("ArabicUnitCount"),IC(1))));
        p.Emit(Assign2(22,"ArabicCurrentUnit",c.Add(StateR("ArabicCurrentUnit"),1),"Int",true));
        p.Jump("finish",c.Less(StateR("ArabicCurrentUnit"),StateR("ArabicUnitCount")));p.Emit(Call2(c.Functions[Helpers2[5]],StateR("ArabicCurrentUnit")));
        p.Jump("return",c.IntEq(StateR("ArabicCurrentUnit"),c.C("KismetMathLibrary","Subtract_IntInt",StateR("ArabicUnitCount"),IC(1))));
        p.Mark("finish");p.Emit(Call2(c.Functions["Arabic Finish"],BC(false)));p.Mark("return");p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Advance Budget",null,("Float","DeltaSeconds"),("Int","Generation"));f=p.ExportIndex;c.Local(f,"Float","Due");
        p.Jump("return",c.And(c.And(StateR("ArabicSchedulerArmed"),StateR("bArabicActive")),c.IntEq(Var2(f,"Generation"),StateR("ArabicGeneration"))));
        p.Jump("return",c.C("KismetMathLibrary","GreaterEqual_FloatFloat",Var2(f,"DeltaSeconds"),FC(0)));
        p.Emit(Assign2(22,"ArabicElapsed",c.C("KismetMathLibrary","Add_FloatFloat",StateR("ArabicElapsed"),Var2(f,"DeltaSeconds")),"Float",true));
        p.Mark("loop");p.Jump("return",c.And(c.And(StateR("bArabicActive"),StateR("ArabicSchedulerArmed")),c.IntEq(Var2(f,"Generation"),StateR("ArabicGeneration"))));
        p.Jump("finish",c.Less(c.Add(StateR("ArabicCurrentUnit"),1),StateR("ArabicUnitCount")));
        p.Emit(c.C("KismetArrayLibrary","Array_Get",StateR("ArabicUnitDelays"),c.Add(StateR("ArabicCurrentUnit"),1),Var2(f,"Due")));
        p.Jump("return",c.C("KismetMathLibrary","GreaterEqual_FloatFloat",StateR("ArabicElapsed"),Var2(f,"Due")));
        p.Emit(Assign2(22,"ArabicElapsed",c.C("KismetMathLibrary","Subtract_FloatFloat",StateR("ArabicElapsed"),Var2(f,"Due")),"Float",true));p.Emit(Call2(c.Functions["Arabic Step"]));p.Jump("loop");
        p.Mark("finish");p.Emit(Call2(c.Functions["Arabic Finish"],BC(false)));p.Mark("return");p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Advance Clocks",null,("Float","WorldDelta"),("Float","PausedDelta"),("Int","Generation"));f=p.ExportIndex;
        // Unbound clock-port contract only. No engine tick/timer callback or pause equivalence is claimed.
        p.Jump("world",StateR("Animate While Paused"));p.Emit(Call2(c.Functions["Arabic Advance Budget"],Var2(f,"PausedDelta"),Var2(f,"Generation")));p.Jump("return");
        p.Mark("world");p.Emit(Call2(c.Functions["Arabic Advance Budget"],Var2(f,"WorldDelta"),Var2(f,"Generation")));p.Mark("return");p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Begin Reveal",null);p.Emit(Assign2(22,"ArabicFinished",BC(false),"Bool",true));p.Emit(Assign2(22,"ArabicElapsed",FC(0),"Float",true));
        p.Emit(Assign2(22,"ArabicCurrentUnit",StateR("ArabicThreshold"),"Int",true));p.Emit(Assign2(22,"ArabicSchedulerArmed",BC(true),"Bool",true));
        p.Jump("finish",c.Less(StateR("ArabicCurrentUnit"),c.C("KismetMathLibrary","Subtract_IntInt",StateR("ArabicUnitCount"),IC(1))));
        p.Emit(Call2(c.Functions["Arabic Advance Budget"],FC(0),StateR("ArabicGeneration")));p.Jump("return");p.Mark("finish");p.Emit(Call2(c.Functions["Arabic Finish"],BC(false)));p.Mark("return");p.Emit(Return2());p.Emit(X("EndOfScript"));
    }

    static void GenerateStyleR(Build2Context c,JsonObject baseline) {
        var script=Arr(Export(baseline,"Set Displayed Line"),"ScriptBytecode");int first=script.Select((n,i)=>(n,i)).Single(x=>IsAssignmentR(x.n!,"ARLarge")).i;
        int end=script.Select((n,i)=>(n,i)).First(x=>x.i>first&&Num(x.n!["StackNode"]??V(0))==c.Functions[Helpers2[5]]).i;
        var p=c.Function("Arabic Apply Style",null);int f=p.ExportIndex;c.Local(f,"Bool","ARLarge");
        var property=Copy(Arr(Export(baseline,"Set Displayed Line"),"LoadedProperties").Single(x=>Str(x!["Name"])=="ARForegroundStyle")!);Arr(Arr(c.Asset,"Exports")[f-1]!,"LoadedProperties").Add(property);
        p.Original=script.DeepClone().AsArray();p.SourceExportIndex=11;
        for(int i=first;i<end;i++){p.Old(i);Rebind2(p.Cells[^1].Code,11,f,n=>n);}
        p.Mark("old_"+end);
        foreach(string w in new[]{Widgets[3],Widgets[4]})p.Emit(Method2(w,c.N("RetainerBox","SetRetainRendering"),c.Not(StateR("Has Outline"))));
        p.Jump("visible",StateR("Has Outline"));p.Emit(Visible2(Widgets[3],2));p.Jump("render");p.Mark("visible");p.Emit(Visible2(Widgets[3],0));p.Mark("render");
        foreach(string w in new[]{Widgets[3],Widgets[4]})p.Emit(Method2(w,c.N("RetainerBox","RequestRender")));p.Emit(Return2());p.Emit(X("EndOfScript"));
        p=c.Function("Arabic Apply Wrap",null);foreach(string w in new[]{Widgets[2],Widgets[6]})p.Emit(Call2(-38,StateR(w),StateR("Wrap Text Length")));p.Emit(Return2());p.Emit(X("EndOfScript"));
    }

    static void ExtendEntriesR(Build2Context c,JsonObject baseline,string root) {
        var source=Arr(Export(baseline,"Set Displayed Line"),"ScriptBytecode");var originalGame=JsonNode.Parse(File.ReadAllText(Path.Combine(root,"builds/rtl_poc/stage1/original_wbp_baseline.json")))!;
        var p=new Asm2{ExportIndex=11,Original=source.DeepClone().AsArray()};c.Plans.Add(p);
        for(int i=0;i<source.Count;i++) {
            if(Str(source[i]!["FunctionName"])==Helpers2[0])p.Emit(Call2(c.Functions["Arabic Cancel"]));
            p.Old(i);
            bool speakerThreshold=Num(source[i]!["StackNode"]??V(0))==c.Functions[Helpers2[5]] && Str(source[i]!["Parameters"]?[0]).Contains("ArabicSpeakerUnits");
            if(speakerThreshold) {
                // Original initialization is retained; only scheduler setup is appended on its Arabic tail.
                p.Emit(Call2(c.Functions["Build Arabic Timing"],Var2(11,"ARPlain"),Var2(11,"ARSpeaker")));
                p.Emit(Call2(c.Functions["Arabic Apply Wrap"]));p.Emit(Call2(c.Functions["Arabic Begin Reveal"]));
                foreach(int k in new[]{23,24,25})p.Emit(Copy(originalGame["Exports"]![10]!["ScriptBytecode"]![k]!));
                p.Jump("animation_enabled",c.Not(Var2(11,"CallFunc_GetOptionValue_ReturnValue_2")));p.Emit(Call2(c.Functions["Arabic Finish"],BC(true)));p.Mark("animation_enabled");
            }
        }
        foreach(var (name,helper) in new[]{("Stop Displaying Line","Arabic Cancel"),("Set Has Outline","Arabic Apply Style"),("ChangeTextToLarge","Arabic Apply Style"),("Set Wrap Text At","Arabic Apply Wrap")}) {
            var fn=Export(baseline,name);int index=Index(baseline,name);var code=Arr(fn,"ScriptBytecode");p=new Asm2{ExportIndex=index,Original=code.DeepClone().AsArray()};c.Plans.Add(p);
            for(int i=0;i<code.Count;i++) {
                bool hook=IsOpR(code[i]!,"Return");
                if(hook){p.Mark("old_"+i);if(name!="Stop Displaying Line")p.Jump("after_hook",StateR("bArabicProtoSuppressed"));p.Emit(Call2(c.Functions[helper]));p.Mark("after_hook");}
                p.Old(i);if(hook)p.Cells[^1].Label="return_original_"+i;
            }
        }
        // A prior Proto line must not finish/release a block now owned by the Arabic path.
        var oldEvent=Export(baseline,"On Text Finished Letter by Letter Print");var eventCode=Arr(oldEvent,"ScriptBytecode");
        p=new Asm2{ExportIndex=Index(baseline,"On Text Finished Letter by Letter Print"),Original=eventCode.DeepClone().AsArray()};c.Plans.Add(p);
        p.Jump("old_0",StateR("bArabicProtoSuppressed"));p.Emit(Return2());for(int i=0;i<eventCode.Count;i++)p.Old(i);
    }

    static JsonObject RevealProjection(JsonObject n)=>Projection(n);
    static List<string> CheckReveal(JsonObject actual,JsonObject baseline,string root) {
        var errors=new List<string>();void T(bool ok,string why){if(!ok)errors.Add(why);}
        var expected=GenerateReveal(baseline,root);T(JsonNode.DeepEquals(RevealProjection(actual),RevealProjection(Normalize(expected.Asset))),"unexpected reveal schema change");
        T(Arr(actual,"NameMap").Take(Arr(baseline,"NameMap").Count).Select(Str).SequenceEqual(Arr(baseline,"NameMap").Select(Str)),"frozen name indices changed");
        T(JsonNode.DeepEquals(new JsonArray(Arr(actual,"Imports").Take(Arr(baseline,"Imports").Count).Select(x=>x!.DeepClone()).ToArray()),baseline["Imports"]),"frozen imports changed");
        if(RevealInvariantsR(actual,baseline,expected.Functions,new[]{"Arabic Step","Arabic Advance Budget","Arabic Advance Clocks","Arabic Finish"},T))return errors;
        RevealBytecodeR(actual,baseline,expected.Plans,T);
        foreach(var old in Arr(baseline,"Exports").Where(x=>Str(x!["$type"]).Contains("FunctionExport"))){int i=Index(baseline,Str(old!["ObjectName"]));if(!new[]{4,11,12,14,19,21}.Contains(i))T(JsonNode.DeepEquals(old["ScriptBytecode"],Export(actual,Str(old["ObjectName"]))["ScriptBytecode"]),"unrelated function changed");}
        DependencyCycles(actual,errors);return errors;
    }
    // Shared by the 011 reveal validator and the 012 clock validator; returns true when references dangle.
    static bool RevealInvariantsR(JsonObject actual,JsonObject baseline,Dictionary<string,int> functions,IEnumerable<string> paced,Action<bool,string> T) {
        bool dangling=false;
        foreach(int r in References(actual["Exports"]).Concat(References(actual["Imports"])).Concat(ScriptReferences2(actual["Exports"])))if(!(r>=-Arr(actual,"Imports").Count&&r<=Arr(actual,"Exports").Count)){T(false,"dangling reveal reference");dangling=true;}
        foreach(string name in paced)JsonWalk2(Export(actual,name)["ScriptBytecode"],"$",(o,_)=>{
            int index=Num(o["StackNode"]??V(0));if(index<0&&-index<=Arr(actual,"Imports").Count){string call=Str(Arr(actual,"Imports")[-index-1]!["ObjectName"]);T(call is not ("SetText" or "SetTextStyleSet"),"reveal-time SetText/style mutation");}
        });
        var finish=Arr(Export(actual,"Arabic Finish"),"ScriptBytecode");T(finish.Any(x=>IsOpR(x!,"JumpIfNot"))&&finish.Any(x=>IsAssignmentR(x!,"ArabicFinished")),"missing idempotent finish guard");
        T(finish.Count(x=>IsOpR(x!,"CallMulticastDelegate"))==1,"double finish broadcast");
        foreach(string name in new[]{"Arabic Finish","Arabic Cancel"})T(Arr(Export(actual,name),"ScriptBytecode").Any(x=>IsAssignmentR(x!,"ArabicSchedulerArmed")&&IsOpR(x!["AssignmentExpression"]!,"False")),"missing scheduler clear");
        T(Arr(Export(actual,"Stop Displaying Line"),"ScriptBytecode").Any(x=>Num(x!["StackNode"]??V(0))==functions["Arabic Cancel"]),"Stop does not clear scheduler");
        T(Arr(Export(actual,"Arabic Skip"),"ScriptBytecode").Any(x=>Num(x!["StackNode"]??V(0))==functions["Arabic Finish"]),"skip does not reach Finish");
        foreach(string name in new[]{"ArabicFinished","ArabicSchedulerArmed","ArabicCurrentUnit","ArabicUnitCount","ArabicSpeakerUnits","ArabicElapsed","bArabicActive","ArabicGeneration"})T(Arr(Export(actual,"Arabic Cancel"),"ScriptBytecode").Any(x=>IsAssignmentR(x!,name)),"missing pool reset "+name);
        T(Arr(Export(actual,"Arabic Cancel"),"ScriptBytecode").Any(x=>IsOpR(x!,"SetArray")&&Arr(x!,"Elements").Count==0),"missing pool reset ArabicUnitDelays");
        var threshold=Export(actual,Helpers2[5]);T(JsonNode.DeepEquals(threshold["ScriptBytecode"],Export(baseline,Helpers2[5])["ScriptBytecode"]),"unpaired shadow threshold update");
        return dangling;
    }
    static void RevealBytecodeR(JsonObject actual,JsonObject baseline,List<Asm2> plans,Action<bool,string> T) {
        foreach(var e in Arr(actual,"Exports").Where(x=>x!["ScriptBytecode"]!=null))JsonWalk2(e!["ScriptBytecode"],"$",(node,_)=>{
            if(Str(node["$type"]).Contains("FFieldPath")&&Num(node["ResolvedOwner"])>0){int owner=Num(node["ResolvedOwner"]);foreach(var field in Arr(node,"Path").Take(1))T(Arr(Arr(actual,"Exports")[owner-1]!,"LoadedProperties").Any(p=>Str(p!["Name"])==Str(field)),"unresolved reveal variable "+Str(field));}
            if(node["StackNode"] is JsonValue && Num(node["StackNode"])<0){var import=Arr(actual,"Imports")[-Num(node["StackNode"])-1]!;T(Str(import["ClassName"])=="Function","unresolved reveal function");}
        });
        var typed=UAsset.DeserializeJson(actual.ToJsonString());
        foreach(var p in plans) {
            var expr=((StructExport)typed.Exports[p.ExportIndex-1]).ScriptBytecode!;int[] offsets=new int[expr.Length+1];for(int i=0;i<expr.Length;i++)offsets[i+1]=offsets[i]+Size2(typed,expr[i]);
            var script=Arr(Arr(actual,"Exports")[p.ExportIndex-1]!,"ScriptBytecode");if(script.Count!=expr.Length)continue;
            T(Num(Arr(actual,"Exports")[p.ExportIndex-1]!["ScriptBytecodeSize"])==offsets[^1],"incorrect reveal logical size");
            if(p.ExportIndex<=Arr(baseline,"Exports").Count&&p.Original!=null&&script.Count==p.Cells.Count)
                for(int i=0;i<p.Cells.Count;i++)if(p.Cells[i].OriginalIndex is int oi)T(JsonNode.DeepEquals(Semantic2(script[i]),Semantic2(p.Original[oi])),"original continuation instruction altered "+p.ExportIndex+":"+oi);
            for(int i=0;i<expr.Length;i++){var nodes=new Dictionary<string,UAssetAPI.Kismet.Bytecode.KismetExpression>();TypedWalk2(expr[i],"$",nodes);JsonWalk2(script[i],"$",(node,path)=>{
                if(IsOpR(node,"Context"))T(Num(node["Offset"])==Size2(typed,nodes[path+".ContextExpression"]),"bad reveal context skip");
                if(IsOpR(node,"Jump")||IsOpR(node,"JumpIfNot")||IsOpR(node,"PushExecutionFlow")){int target=Num(node[IsOpR(node,"PushExecutionFlow")?"PushingAddress":"CodeOffset"]);T(Array.IndexOf(offsets,target)>=0&&target<offsets[^1],"bad scheduler jump");}
            });}
        }
    }
    static JsonArray DiffReveal(string originalPath,string generatedPath) {
        var original=Read(originalPath);var generated=Read(generatedPath);var result=new JsonArray();
        var old=File.ReadAllBytes(originalPath).Concat(File.ReadAllBytes(Path.ChangeExtension(originalPath,".uexp"))).ToArray();var now=File.ReadAllBytes(generatedPath).Concat(File.ReadAllBytes(Path.ChangeExtension(generatedPath,".uexp"))).ToArray();
        for(int i=0;i<original.Exports.Count;i++){
            var o=original.Exports[i];var n=generated.Exports[i];var before=old.AsSpan((int)o.SerialOffset,(int)o.SerialSize).ToArray();var after=now.AsSpan((int)n.SerialOffset,(int)n.SerialSize).ToArray();bool same=before.SequenceEqual(after);Require(same||new[]{4,11,12,14,19,21,22,23}.Contains(i+1),"unexpected reveal export change "+(i+1));
            var item=new JsonObject{["export"]=i+1,["name"]=o.ObjectName.ToString(),["classification"]=same?"BYTE_IDENTICAL":"EXPECTED_ADDITIVE_REVEAL_CHANGE",["source_payload_sha256"]=Hash(before),["generated_payload_sha256"]=Hash(after)};
            if(o is FunctionExport of&&n is FunctionExport nf){var b=Bytecode(original,of,out _);var a=Bytecode(generated,nf,out _);item["source_bytecode_sha256"]=Hash(b);item["generated_bytecode_sha256"]=Hash(a);item["bytecode_unchanged"]=b.SequenceEqual(a);if(!new[]{4,11,12,14,19,21}.Contains(i+1))Require(b.SequenceEqual(a),"untouched reveal function changed "+(i+1));}result.Add(item);
        }return result;
    }
    static JsonArray NegativeReveal(JsonObject good,JsonObject baseline,string root) {
        var results=new JsonArray();void Run(string name,Action<JsonObject> mutate,string diagnostic){var bad=Copy(good);mutate(bad);var errors=CheckReveal(bad,baseline,root);Require(errors.Any(x=>x.Contains(diagnostic)),"negative fixture missed "+name);results.Add(new JsonObject{["fixture"]=name,["detected"]=true,["diagnostics"]=new JsonArray(errors.Take(5).Select(x=>(JsonNode)V(x)).ToArray())});}
        Run("double-finish broadcast",a=>{var s=Arr(Export(a,"Arabic Finish"),"ScriptBytecode");s.Insert(s.Count-2,s.Single(x=>IsOpR(x!,"CallMulticastDelegate"))!.DeepClone());},"double finish broadcast");
        Run("missing scheduler clear",a=>{var n=Arr(Export(a,"Arabic Cancel"),"ScriptBytecode").Single(x=>IsAssignmentR(x!,"ArabicSchedulerArmed"))!;n["AssignmentExpression"]=BC(true);},"missing scheduler clear");
        Run("bad scheduler jump",a=>Arr(Export(a,"Arabic Advance Budget"),"ScriptBytecode").First(x=>IsOpR(x!,"JumpIfNot"))!["CodeOffset"]=3,"bad scheduler jump");
        Run("unpaired shadow update",a=>{var s=Arr(Export(a,Helpers2[5]),"ScriptBytecode");s.Remove(s.First(x=>Str(x).Contains("ArabicShadowBorder")));},"unpaired shadow threshold update");
        Run("SetText inside Arabic Step",a=>Arr(Export(a,"Arabic Step"),"ScriptBytecode").Insert(0,Method2(Widgets[2],-128,SC("bad"))),"reveal-time SetText/style mutation");
        Run("missing pool reset",a=>{var s=Arr(Export(a,"Arabic Cancel"),"ScriptBytecode");s.Remove(s.Single(x=>IsAssignmentR(x!,"ArabicUnitCount")));},"missing pool reset ArabicUnitCount");
        return results;
    }
    public static int BuildReveal(string rootPath,string outputDirectory) {
        try{string root=Path.GetFullPath(rootPath),dir=Path.GetFullPath(outputDirectory);Require(dir.StartsWith(Path.GetFullPath(Path.Combine(root,"builds/rtl_poc"))+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase),"detached output required");Require(!Directory.Exists(dir),"refusing existing files");
            var frozen=Directory.GetFiles(Path.Combine(root,"builds/rtl_poc/stage1"),"*",SearchOption.AllDirectories).Concat(Directory.GetFiles(Path.Combine(root,"builds/rtl_poc/stage2"),"*",SearchOption.AllDirectories)).OrderBy(x=>x,StringComparer.Ordinal).ToArray();var hashes=frozen.Select(HashFile).ToArray();
            var source=Path.Combine(root,"builds/rtl_poc/stage2",Wbp2+".uasset");var baseline=Model(Read(source));var c=GenerateReveal(baseline,root);Directory.CreateDirectory(dir);File.WriteAllText(Path.Combine(dir,"NOT_INSTALLABLE.txt"),"REVEAL PARTIAL OFFLINE NOT_INSTALLABLE NOT_RUNTIME_TESTED\nClock bridge is unbound: original pause accumulator source NOT_PROVEN.\n");
            WritePackage(c.Asset,RevealPath(dir));var a=Model(Read(RevealPath(dir)));var errors=CheckReveal(a,baseline,root);Require(errors.Count==0,string.Join(";",errors.Take(12)));
            string repeat=Path.Combine(dir,"determinism"),roundtrip=Path.Combine(dir,"roundtrip");WritePackage(GenerateReveal(baseline,root).Asset,RevealPath(repeat));Directory.CreateDirectory(roundtrip);Read(RevealPath(dir)).Write(RevealPath(roundtrip));
            foreach(string extension in new[]{".uasset",".uexp"})foreach(string target in new[]{repeat,roundtrip})Require(File.ReadAllBytes(Path.ChangeExtension(RevealPath(dir),extension)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(RevealPath(target),extension))),"reveal determinism/roundtrip");
            SaveJson(Path.Combine(dir,"instruction_inventory.json"),InstructionInventory(Read(RevealPath(dir))));
            var diff=DiffReveal(source,RevealPath(dir));Require(hashes.SequenceEqual(frozen.Select(HashFile)),"Stage1/Stage2 input changed");
            SaveJson(Path.Combine(dir,"reveal_verification.json"),new JsonObject{["status"]="R8B_WBP_STAGE2_REVEAL_PARTIAL",["clock_adapter_bound"]=false,["pause_equivalence_proven"]=false,["validator_errors"]=0,["negative_tests"]=NegativeReveal(a,baseline,root),["original_export_diff"]=diff,["frozen_inputs"]=new JsonArray(frozen.Select((p,i)=>(JsonNode)new JsonObject{["path"]=Path.GetRelativePath(root,p),["sha256"]=hashes[i]}).ToArray()),["deterministic"]=true,["roundtrip"]=true,["uasset_sha256"]=HashFile(RevealPath(dir)),["uexp_sha256"]=HashFile(Path.ChangeExtension(RevealPath(dir),".uexp")),["DISPATCH_INTEGRATION_PROVEN"]=false,["IN_GAME_RTL_PROVEN"]=false,["tested_in_game"]=0,["final"]=0});Console.WriteLine("R8B_WBP_STAGE2_REVEAL_PARTIAL: control helpers generated; native pause clock adapter unbound. "+dir);return 0;
        }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}
    }
    public static int ValidateReveal(string rootPath,string directory) {
        try{string root=Path.GetFullPath(rootPath),dir=Path.GetFullPath(directory);string sourcePath=Path.Combine(root,"builds/rtl_poc/stage2",Wbp2+".uasset");var source=Model(Read(sourcePath));var a=Read(RevealPath(dir));Require(a.VerifyBinaryEquality(),"reveal binary roundtrip");var errors=CheckReveal(Model(a),source,root);Require(errors.Count==0,string.Join(";",errors));var report=JsonNode.Parse(File.ReadAllText(Path.Combine(dir,"reveal_verification.json")))!;foreach(var entry in Arr(report,"frozen_inputs"))Require(HashFile(Path.Combine(root,Str(entry!["path"])))==Str(entry["sha256"]),"frozen input hash changed");foreach(string ext in new[]{".uasset",".uexp"})foreach(string copy in new[]{"determinism","roundtrip"})Require(File.ReadAllBytes(Path.ChangeExtension(RevealPath(dir),ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(RevealPath(Path.Combine(dir,copy)),ext))),"reveal binary evidence mismatch");Console.WriteLine(new JsonObject{["status"]="REVEAL_CONTROL_STRUCTURE_PASS_CLOCK_UNBOUND",["errors"]=0,["negative_tests"]=NegativeReveal(Model(a),source,root),["original_export_diff"]=DiffReveal(sourcePath,RevealPath(dir))}.ToJsonString(Pretty));return 0;}catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}
    }
}
