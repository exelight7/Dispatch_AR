// UE4.27 ISOLATED TEST - NOT DISPATCH. Built and run on UE 5.8.4 this round (no UE4.27 install): results are NON-AUTHORITATIVE for 4.27.
// Gate harness for the stock-renderer Arabic reveal route (G1/G2/G3/G5 + culture API).
// It authors stock assets (font, UI material, MICs, render target, RichText DataTables) under /Game/ArabicReveal,
// draws stock URichTextBlock / URetainerBox widgets offscreen with FWidgetRenderer and diffs the pixels.
// Only engine UFUNCTIONs that Blueprint can call drive the reveal: URichTextBlock::SetText/SetTextStyleSet (init only)
// and UKismetRenderingLibrary::ClearRenderTarget2D (every step).
// Run: UnrealEditor-Cmd.exe RevealTest.uproject -ExecCmds="Automation RunTests RevealGate.All;Quit" -unattended -nopause -nosplash

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#if WITH_EDITOR
#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/Border.h"
#include "Components/RetainerBox.h"
#include "Components/RichTextBlock.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Dom/JsonObject.h"
#include "Editor.h"
#include "Engine/DataTable.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"
#include "Engine/TextureRenderTarget2D.h"
#include "ImageCore.h"
#include "ImageUtils.h"
#include "Kismet/KismetInternationalizationLibrary.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "ShaderCompiler.h"
#include "Slate/WidgetRenderer.h"
#include "TextureResource.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RevealGate
{
const FString AssetRoot = TEXT("/Game/ArabicReveal");
const int32 NumUnitRows = 255; // unit i is stored as byte i+1 so the colour compensation never divides by 0
const int32 TextSize = 28;
const int32 DebugTextSize = 64;
const float ThrAll = 10000.f;
const FIntPoint LineSize(1000, 300);
const FIntPoint StressSize(1600, 900);
const FIntPoint DebugSize(480, 160);

using FJson = TSharedPtr<FJsonObject>;
using FJsonArr = TArray<TSharedPtr<FJsonValue>>;

FJson Obj() { return MakeShared<FJsonObject>(); }
TSharedPtr<FJsonValue> Num(double V) { return MakeShared<FJsonValueNumber>(V); }
TSharedPtr<FJsonValue> Val(FJson O) { return MakeShared<FJsonValueObject>(O); }

float SrgbToLin(float S) { return S <= 0.04045f ? S / 12.92f : FMath::Pow((S + 0.055f) / 1.055f, 2.4f); }
float LinToSrgb(float L) { return L <= 0.0031308f ? L * 12.92f : 1.055f * FMath::Pow(L, 1.f / 2.4f) - 0.055f; }

// Encodings of unit index i into the row colour R channel (written into FTextBlockStyle::ColorAndOpacity).
float Encode(int32 Enc, int32 I) { return Enc == 0 ? I / 255.f : SrgbToLin(I / 255.f); }
// Decodings mirrored exactly by the material's Custom node (DecodeMode parameter).
int32 Decode(int32 Dec, float R)
{
	const float V = Dec == 0 ? R : (Dec == 1 ? LinToSrgb(R) : SrgbToLin(R));
	return FMath::FloorToInt(V * 255.f + 0.5f);
}

const TCHAR* RevealHlsl = TEXT(
	"float r = VC.r;\n"
	"float s = (r <= 0.0031308) ? r * 12.92 : 1.055 * pow(r, 1.0 / 2.4) - 0.055;\n"
	"float l = (r <= 0.04045) ? r / 12.92 : pow((r + 0.055) / 1.055, 2.4);\n"
	"float v = (Dec < 0.5) ? r : ((Dec < 1.5) ? s : l);\n"
	"float idx = floor(v * 255.0 + 0.5) - 1.0;\n"
	"if (Dbg > 1.5) return float4(1.0, 1.0, 1.0, 1.0);\n"
	"if (Dbg > 0.5) return float4(VC, 1.0);\n"
	"float vis = (idx <= Thr + 0.25) ? 1.0 : 0.0;\n"
	"return float4(Col / max(VC, 1e-6), vis);\n"); // Slate multiplies the output by the vertex colour (and alpha): undo the RGB part

// Round 008 (R8) variant: no render target. The threshold arrives in VertexColor.G from a per-block Border tint
// (1, srgb_to_linear((t+1)/255), 1, 1); the unit index stays in VertexColor.R from the row colour. Both decoded the same way.
const TCHAR* RevealTintHlsl = TEXT(
	"float3 s = (VC <= 0.0031308) ? VC * 12.92 : 1.055 * pow(VC, 1.0 / 2.4) - 0.055;\n"
	"float idx = floor(s.r * 255.0 + 0.5) - 1.0;\n"
	"float thr = floor(s.g * 255.0 + 0.5) - 1.0;\n"
	"if (Dbg > 1.5) return float4(1.0, 1.0, 1.0, 1.0);\n"
	"if (Dbg > 0.5) return float4(VC, 1.0);\n"
	"float vis = (idx <= thr + 0.25) ? 1.0 : 0.0;\n"
	"return float4(Col / max(VC, 1e-6), vis);\n");

// R8b (round 008): mirror of DISPATCH's shipped M_SubtitlePrinting pixel math, read from its compiled DXBC:
// emissive = Color / VertexColor, opacity = saturate((VertexColor.b - 0.1) * 1.11). The 4.27 VS floors VC at 6.1e-5 before
// linearising, so max(VC, 1e-6) here stands in for that floor. Reveal code: row B = K^-i, Border tint B = K^t (product packed once).
const TCHAR* RevealPrintingHlsl = TEXT(
	"if (Dbg > 1.5) return float4(1.0, 1.0, 1.0, 1.0);\n"
	"if (Dbg > 0.5) return float4(VC, 1.0);\n"
	"return float4(Col / max(VC, 1e-6), saturate((VC.b - 0.1) * 1.11));\n");

// 0 = R8 (index in R from the row, threshold in G from the Border tint); 1 = R8b (exponential code in B, see above).
int32 Scheme = 0;
const float KB = 10.5f;
const int32 MaxUnitsB = 37; // KB^36 must stay below FLT_MAX

FLinearColor UnitColor(int32 I) { return Scheme == 0 ? FLinearColor(Encode(1, I + 1), 1.f, 1.f, 1.f) : FLinearColor(1.f, 1.f, FMath::Pow(KB, -(float)I), 1.f); }

bool IsLetter(TCHAR C)
{
	return (C >= 'A' && C <= 'Z') || (C >= 'a' && C <= 'z') || (C >= 0x0620 && C <= 0x064A) || (C >= 0x066E && C <= 0x06D3) ||
		(C >= 0x0750 && C <= 0x077F) || (C >= 0xFB50 && C <= 0xFDFF) || (C >= 0xFE70 && C <= 0xFEFC);
}

// Whitespace-only unit segmentation: <uN>word</> with the whitespace left outside the tags (Default row).
// A token without a letter (digits, lone punctuation) joins the previous unit so no unit lacks a strong letter.
FString BuildMarkup(const FString& Text, int32& OutUnits)
{
	struct FTok { FString Word, Gap; };
	TArray<FTok> Toks;
	FString Lead;
	int32 I = 0;
	while (I < Text.Len() && FChar::IsWhitespace(Text[I])) Lead.AppendChar(Text[I++]);
	while (I < Text.Len())
	{
		FTok T;
		while (I < Text.Len() && !FChar::IsWhitespace(Text[I])) T.Word.AppendChar(Text[I++]);
		while (I < Text.Len() && FChar::IsWhitespace(Text[I])) T.Gap.AppendChar(Text[I++]);
		bool bLetter = false;
		for (TCHAR C : T.Word) bLetter |= IsLetter(C);
		if (!bLetter && Toks.Num() > 0 && !Toks.Last().Gap.Contains(TEXT("\n")))
		{
			Toks.Last().Word += Toks.Last().Gap + T.Word;
			Toks.Last().Gap = T.Gap;
		}
		else
		{
			Toks.Add(T);
		}
	}
	const int32 MaxUnits = Scheme == 1 ? MaxUnitsB : NumUnitRows;
	if (Toks.Num() > MaxUnits) // overflow: the tail becomes one last unit
	{
		for (int32 K = MaxUnits; K < Toks.Num(); ++K)
		{
			Toks[MaxUnits - 1].Word += Toks[MaxUnits - 1].Gap + Toks[K].Word;
			Toks[MaxUnits - 1].Gap = Toks[K].Gap;
		}
		Toks.SetNum(MaxUnits);
	}
	FString Out = Lead;
	for (int32 U = 0; U < Toks.Num(); ++U) Out += FString::Printf(TEXT("<u%d>%s</>%s"), U, *Toks[U].Word, *Toks[U].Gap);
	OutUnits = Toks.Num();
	return Out;
}

struct FShot
{
	int32 W = 0, H = 0;
	TArray<FLinearColor> Px;
};

bool Vis(const FLinearColor& C) { return C.A > 0.f || C.R > 0.f || C.G > 0.f || C.B > 0.f; }

struct FHarness
{
	FAutomationTestBase* Test = nullptr;
	UWorld* World = nullptr;
	FString OutDir;
	TUniquePtr<FWidgetRenderer> Renderer;
	TMap<FIntPoint, UTextureRenderTarget2D*> Targets;
	TMap<int32, FShot> Labels;
	UTextureRenderTarget2D* RevealRT = nullptr;
	UFont* Font = nullptr;
	UMaterial* Material = nullptr;
	TSet<UWidget*> Warm;
	int32 FirstPaints = 0, FirstPaintsDiffering = 0, FirstPaintsEmptyThenNot = 0;
	int32 SetTextCalls = 0;
	int32 SetStyleCalls = 0;
	FJson Results = Obj();
	FString PackageRoot = AssetRoot;
	TFunction<void(float)> ThresholdOverride; // R8: threshold written as a widget tint instead of the RT

	// ---------- asset authoring ----------
	template <class T> T* NewAsset(const FString& Name)
	{
		UPackage* Pkg = CreatePackage(*(PackageRoot / Name));
		Pkg->FullyLoad();
		T* A = NewObject<T>(Pkg, *Name, RF_Public | RF_Standalone);
		FAssetRegistryModule::AssetCreated(A);
		return A;
	}

	void Save(UObject* A)
	{
		UPackage* Pkg = A->GetOutermost();
		Pkg->MarkPackageDirty();
		const FString File = FPackageName::LongPackageNameToFilename(Pkg->GetName(), FPackageName::GetAssetPackageExtension());
		FSavePackageArgs Args;
		Args.TopLevelFlags = RF_Public | RF_Standalone;
		if (!UPackage::SavePackage(Pkg, A, *File, Args)) Test->AddError(FString::Printf(TEXT("Save failed: %s"), *File));
	}

	UFontFace* MakeFace(const FString& Name, const FString& Ttf)
	{
		TArray<uint8> Data;
		if (!FFileHelper::LoadFileToArray(Data, *Ttf)) Test->AddError(TEXT("Missing font ") + Ttf);
		UFontFace* Face = NewAsset<UFontFace>(Name);
		Face->SourceFilename = Ttf;
		Face->LoadingPolicy = EFontLoadingPolicy::Inline;
		Face->FontFaceData->SetData(MoveTemp(Data));
		Face->CacheSubFaces();
		Save(Face);
		return Face;
	}

	void MakeFont()
	{
		const FString Dir = FPaths::EngineContentDir() / TEXT("Slate/Fonts");
		UFontFace* Latin = MakeFace(TEXT("FF_Roboto_Regular"), Dir / TEXT("Roboto-Regular.ttf"));
		UFontFace* Arabic = MakeFace(TEXT("FF_NotoNaskhArabicUI_Regular"), Dir / TEXT("NotoNaskhArabicUI-Regular.ttf"));
		Font = NewAsset<UFont>(TEXT("F_ArabicReveal"));
		Font->FontCacheType = EFontCacheType::Runtime;
		FTypefaceEntry& D = Font->CompositeFont.DefaultTypeface.Fonts.AddDefaulted_GetRef();
		D.Name = TEXT("Regular");
		D.Font = FFontData(Latin);
		FCompositeSubFont& Sub = Font->CompositeFont.SubTypefaces.AddDefaulted_GetRef();
		for (const FInt32Range& R : {FInt32Range(0x0600, 0x0700), FInt32Range(0x0750, 0x0780), FInt32Range(0x08A0, 0x0900),
				 FInt32Range(0xFB50, 0xFE00), FInt32Range(0xFE70, 0xFF00)})
			Sub.CharacterRanges.Add(R);
		FTypefaceEntry& A = Sub.Typeface.Fonts.AddDefaulted_GetRef();
		A.Name = TEXT("Regular");
		A.Font = FFontData(Arabic);
		Font->PostEditChange();
		Save(Font);
	}

	void MakeRevealRT()
	{
		RevealRT = NewAsset<UTextureRenderTarget2D>(TEXT("RT_ArabicReveal"));
		RevealRT->RenderTargetFormat = RTF_RGBA16f;
		RevealRT->ClearColor = FLinearColor(-1.f, 0.f, 0.f, 1.f); // threshold -1 = nothing revealed
		RevealRT->bAutoGenerateMips = false;
		RevealRT->InitAutoFormat(1, 1);
		RevealRT->UpdateResourceImmediate(true);
		Save(RevealRT);
	}

	void MakeMaterial(const FString& Name = TEXT("M_ArabicReveal"), const TCHAR* Hlsl = RevealHlsl, bool bRT = true)
	{
		UMaterial* M = NewAsset<UMaterial>(Name);
		M->MaterialDomain = MD_UI;
		M->BlendMode = BLEND_Translucent;
		M->SetShadingModel(MSM_Unlit);
		auto Add = [M](UMaterialExpression* E, int32 X, int32 Y) {
			E->Material = M;
			E->MaterialExpressionEditorX = X;
			E->MaterialExpressionEditorY = Y;
			M->GetExpressionCollection().AddExpression(E);
			return E;
		};
		auto* VC = NewObject<UMaterialExpressionVertexColor>(M);
		Add(VC, -700, -200);
		auto* UV = NewObject<UMaterialExpressionConstant2Vector>(M);
		UV->R = 0.5f;
		UV->G = 0.5f;
		Add(UV, -900, 0);
		UMaterialExpressionTextureSampleParameter2D* Tex = nullptr;
		if (bRT)
		{
			Tex = NewObject<UMaterialExpressionTextureSampleParameter2D>(M);
			Tex->ParameterName = TEXT("RevealRT");
			Tex->Texture = RevealRT;
			Tex->SamplerType = SAMPLERTYPE_Color; // engine-required for a render target; RT is RGBA16f linear, so no sRGB decode
			Tex->Coordinates.Expression = UV;
			Add(Tex, -700, 0);
		}
		auto* Dbg = NewObject<UMaterialExpressionScalarParameter>(M);
		Dbg->ParameterName = TEXT("DebugMode");
		Add(Dbg, -700, 250);
		auto* Dec = NewObject<UMaterialExpressionScalarParameter>(M);
		Dec->ParameterName = TEXT("DecodeMode");
		Add(Dec, -700, 350);
		auto* Col = NewObject<UMaterialExpressionVectorParameter>(M);
		Col->ParameterName = TEXT("SubtitleColor");
		Col->DefaultValue = FLinearColor::White;
		Add(Col, -700, 450);
		auto* C = NewObject<UMaterialExpressionCustom>(M);
		C->Code = Hlsl;
		C->OutputType = CMOT_Float4;
		C->Description = TEXT("ArabicReveal");
		C->Inputs.Reset();
		auto In = [C](const TCHAR* Name, UMaterialExpression* E, int32 Out) {
			FCustomInput& I = C->Inputs.AddDefaulted_GetRef();
			I.InputName = Name;
			I.Input.Connect(Out, E);
		};
		In(TEXT("VC"), VC, 0);  // RGB
		In(TEXT("VA"), VC, 4);  // A
		if (bRT) In(TEXT("Thr"), Tex, 1); // R
		In(TEXT("Dbg"), Dbg, 0);
		In(TEXT("Dec"), Dec, 0);
		In(TEXT("Col"), Col, 0); // RGB
		Add(C, -300, 0);
		auto* Rgb = NewObject<UMaterialExpressionComponentMask>(M);
		Rgb->R = Rgb->G = Rgb->B = 1;
		Rgb->A = 0;
		Rgb->Input.Expression = C;
		Add(Rgb, -100, -50);
		auto* Alpha = NewObject<UMaterialExpressionComponentMask>(M);
		Alpha->A = 1;
		Alpha->R = Alpha->G = Alpha->B = 0;
		Alpha->Input.Expression = C;
		Add(Alpha, -100, 50);
		M->GetEditorOnlyData()->EmissiveColor.Expression = Rgb;
		M->GetEditorOnlyData()->Opacity.Expression = Alpha;
		M->PreEditChange(nullptr);
		M->PostEditChange();
		FinishShaders();
		if (const FMaterialResource* Res = M->GetMaterialResource(GMaxRHIShaderPlatform))
			for (const FString& E : Res->GetCompileErrors()) Test->AddError(Name + TEXT(" compile: ") + E);
		Save(M);
		Material = M;
	}

	UMaterialInstanceConstant* MakeMI(const FString& Name, FLinearColor Color, float DebugMode, float DecodeMode)
	{
		UMaterialInstanceConstant* MI = NewAsset<UMaterialInstanceConstant>(Name);
		MI->SetParentEditorOnly(Material);
		MI->SetVectorParameterValueEditorOnly(FMaterialParameterInfo(TEXT("SubtitleColor")), Color);
		MI->SetScalarParameterValueEditorOnly(FMaterialParameterInfo(TEXT("DebugMode")), DebugMode);
		MI->SetScalarParameterValueEditorOnly(FMaterialParameterInfo(TEXT("DecodeMode")), DecodeMode);
		MI->PostEditChange();
		Save(MI);
		return MI;
	}

	// OutlineMat set: DISPATCH-like outline (size 2) whose OutlineColor carries the same unit index as the fill.
	FRichTextStyleRow Row(UMaterialInterface* Mat, int32 Size, FLinearColor Color, UMaterialInterface* OutlineMat = nullptr)
	{
		FRichTextStyleRow R;
		R.TextStyle.Font = FSlateFontInfo(Font, Size);
		R.TextStyle.Font.FontMaterial = Mat;
		if (OutlineMat)
		{
			R.TextStyle.Font.OutlineSettings.OutlineSize = 2;
			R.TextStyle.Font.OutlineSettings.OutlineMaterial = OutlineMat;
			R.TextStyle.Font.OutlineSettings.OutlineColor = Color;
		}
		R.TextStyle.ColorAndOpacity = FSlateColor(Color);
		R.TextStyle.ShadowOffset = FVector2D::ZeroVector;
		return R;
	}

	// One row per unit index; rows differ only in ColorAndOpacity.R (same font, size, material => same metrics).
	UDataTable* MakeTable(const FString& Name, UMaterialInterface* Mat, int32 Size, int32 Enc, bool bAsset, UMaterialInterface* OutlineMat = nullptr)
	{
		UDataTable* DT = bAsset ? NewAsset<UDataTable>(Name) : NewObject<UDataTable>(GetTransientPackage(), *Name);
		if (!bAsset) DT->AddToRoot();
		DT->RowStruct = FRichTextStyleRow::StaticStruct();
		DT->AddRow(TEXT("Default"), Row(Mat, Size, Scheme == 1 ? UnitColor(0) : FLinearColor(Encode(Enc, 1), 1, 1, 1), OutlineMat));
		for (int32 I = 0; I < NumUnitRows; ++I)
			DT->AddRow(*FString::Printf(TEXT("u%d"), I), Row(Mat, Size, Scheme == 1 ? UnitColor(I) : FLinearColor(Encode(Enc, I + 1), 1, 1, 1), OutlineMat));
		if (bAsset) Save(DT);
		return DT;
	}

	void FinishShaders()
	{
		if (GShaderCompilingManager) GShaderCompilingManager->FinishAllCompilation();
		FlushRenderingCommands();
	}

	// ---------- widgets / drawing ----------
	URichTextBlock* MakeText(UDataTable* DT, const FString& Markup)
	{
		URichTextBlock* T = NewObject<URichTextBlock>(GetTransientPackage());
		T->AddToRoot();
		T->SetAutoWrapText(true);
		T->SetJustification(ETextJustify::Center);
		T->SetTextStyleSet(DT);
		++SetStyleCalls;
		T->SetText(FText::FromString(Markup));
		++SetTextCalls;
		return T;
	}

	void SetThreshold(float T)
	{
		if (ThresholdOverride) return ThresholdOverride(T);
		UKismetRenderingLibrary::ClearRenderTarget2D(World, RevealRT, FLinearColor(T, 0.f, 0.f, 1.f));
	}

	// R8 threshold tint: unit t visible iff t <= threshold; -1 = nothing, >= 254 = everything.
	static FLinearColor TintFor(float T)
	{
		const int32 I = FMath::RoundToInt(T);
		if (Scheme == 1) return FLinearColor(1.f, 1.f, I < 0 ? 0.f : FMath::Pow(KB, (float)FMath::Min(I, MaxUnitsB - 1)), 1.f);
		return FLinearColor(1.f, Encode(1, FMath::Clamp(I, -1, 254) + 1), 1.f, 1.f);
	}

	UBorder* MakeTintBorder(UWidget* Content)
	{
		UBorder* B = NewObject<UBorder>(GetTransientPackage());
		B->AddToRoot();
		B->SetPadding(FMargin(0));
		B->SetBrushColor(FLinearColor::Transparent);
		B->SetContent(Content);
		B->SetContentColorAndOpacity(TintFor(-1));
		return B;
	}

	FShot Draw(UWidget* W, FIntPoint Size)
	{
		UTextureRenderTarget2D*& RT = Targets.FindOrAdd(Size);
		if (!RT)
		{
			RT = NewObject<UTextureRenderTarget2D>(GetTransientPackage());
			RT->AddToRoot();
			RT->RenderTargetFormat = RTF_RGBA32f;
			RT->ClearColor = FLinearColor::Transparent;
			RT->bAutoGenerateMips = false;
			RT->InitAutoFormat(Size.X, Size.Y);
			RT->UpdateResourceImmediate(true);
		}
		auto Paint = [&]() {
			Renderer->DrawWidget(RT, W->TakeWidget(), FVector2D(Size), 1.f / 60.f);
			FlushRenderingCommands();
			FShot S;
			S.W = Size.X;
			S.H = Size.Y;
			RT->GameThread_GetRenderTargetResource()->ReadLinearColorPixels(S.Px, FReadSurfaceDataFlags(RCM_UNorm, CubeFace_MAX));
			return S;
		};
		// Observed: the first paint of a new widget can be empty (layout/material proxy not ready). Paint it once more and count it.
		if (!Warm.Contains(W))
		{
			Warm.Add(W);
			const FShot First = Paint();
			FinishShaders(); // material shader permutations used by Slate compile on first use
			Paint();
			const FShot Second = Paint();
			FirstPaints += 1;
			FirstPaintsDiffering += CountDiff(First, Second) != 0;
			FirstPaintsEmptyThenNot += CountVis(First) == 0 && CountVis(Second) > 0;
			return Second;
		}
		return Paint();
	}

	void SavePng(const FShot& S, const FString& Rel)
	{
		FShot* Label = Labels.Find(S.W);
		if (!Label)
		{
			UTextBlock* L = NewObject<UTextBlock>(GetTransientPackage());
			L->AddToRoot();
			L->SetText(FText::FromString(TEXT("UE ISOLATED TEST (UE 5.8.4, NOT 4.27) - NOT DISPATCH")));
			L->SetColorAndOpacity(FSlateColor(FLinearColor(1.f, 0.85f, 0.f, 1.f)));
			Label = &Labels.Add(S.W, Draw(L, FIntPoint(S.W, 28)));
		}
		TArray<FColor> C;
		C.Reserve((Label->H + S.H) * S.W);
		for (const FShot* P : TArray<const FShot*>{Label, &S})
			for (const FLinearColor& L : P->Px)
				C.Add(FColor(FMath::Clamp(FMath::RoundToInt(L.R * 255.f), 0, 255), FMath::Clamp(FMath::RoundToInt(L.G * 255.f), 0, 255),
					FMath::Clamp(FMath::RoundToInt(L.B * 255.f), 0, 255), 255));
		FImageUtils::SaveImageByExtension(*(OutDir / Rel), FImageView(C.GetData(), S.W, Label->H + S.H));
	}

	// white = equal to final reference, red = visible but differs from final, black = hidden
	void SaveDiffPng(const FShot& S, const FShot& Final, const FString& Rel)
	{
		FShot D = S;
		for (int32 I = 0; I < S.Px.Num(); ++I)
			D.Px[I] = !Vis(S.Px[I]) ? FLinearColor::Transparent : (S.Px[I] == Final.Px[I] ? FLinearColor(0.6f, 0.6f, 0.6f, 1) : FLinearColor(1, 0, 0, 1));
		SavePng(D, Rel);
	}

	static int32 CountVis(const FShot& S)
	{
		int32 N = 0;
		for (const FLinearColor& C : S.Px) N += Vis(C);
		return N;
	}

	static float MaxAbsDiff(const FShot& A, const FShot& B)
	{
		float M = 0.f;
		for (int32 I = 0; I < A.Px.Num(); ++I)
			M = FMath::Max(M, FMath::Max(FMath::Max(FMath::Abs(A.Px[I].R - B.Px[I].R), FMath::Abs(A.Px[I].G - B.Px[I].G)),
				FMath::Max(FMath::Abs(A.Px[I].B - B.Px[I].B), FMath::Abs(A.Px[I].A - B.Px[I].A))));
		return M;
	}

	static int32 CountDiff(const FShot& A, const FShot& B)
	{
		int32 N = 0;
		for (int32 I = 0; I < A.Px.Num(); ++I) N += !(A.Px[I] == B.Px[I]);
		return N;
	}

	// Reveal sequence t = -1..Units-1 on one layer. Builds the unit map (pixel -> unit that first lit it) and checks:
	// start blank, no pixel ever disappears, every revealed pixel equals the final reference exactly, every step adds pixels,
	// last step equals the final reference, unit centroids move in reading order (RTL within a line, then down).
	FJson RevealSequence(UWidget* Root, URichTextBlock* Text, int32 Units, FIntPoint Size, const FString& PngDir, TArray<int16>* OutUnitMap,
		TArray<TArray<int32>>* OutVisibleUnits = nullptr, const TArray<int16>* UnitMapIn = nullptr, TFunction<void()> AfterStep = nullptr)
	{
		SetThreshold(ThrAll);
		if (AfterStep) AfterStep();
		FShot Final = Draw(Root, Size);
		int32 StaleFirstCapture = 0;
		if (AfterStep)
		{
			// a RetainerBox may have consumed its RequestRender before the child text was ready: request again, as the WBP must
			AfterStep();
			const FShot Again = Draw(Root, Size);
			StaleFirstCapture = CountDiff(Final, Again);
			Final = Again;
		}
		const FVector2D Desired0 = Text->GetDesiredSize();
		if (!PngDir.IsEmpty()) SavePng(Final, PngDir / TEXT("final.png"));
		TArray<int16> Map;
		Map.Init(-2, Final.Px.Num());
		TArray<bool> Prev;
		Prev.Init(false, Final.Px.Num());
		int32 Mismatch = 0, Removed = 0, EmptySteps = 0, DesiredChanged = 0, OrderViolations = 0;
		float MaxRevealedDiff = 0.f, MaxRevealedDiffAny = 0.f;
		bool bStartBlank = false, bEndEqual = false;
		FJsonArr Steps;
		FVector2D PrevC(-1, -1);
		for (int32 T = -1; T < Units; ++T)
		{
			SetThreshold(T);
			if (AfterStep) AfterStep();
			const FShot S = Draw(Root, Size);
			DesiredChanged += !Text->GetDesiredSize().Equals(Desired0, 0.f);
			int32 Added = 0, StepMismatch = 0;
			double Sx = 0, Sy = 0;
			for (int32 I = 0; I < S.Px.Num(); ++I)
			{
				const bool V = Vis(S.Px[I]);
				if (V && !(S.Px[I] == Final.Px[I]))
				{
					++StepMismatch;
					MaxRevealedDiff = FMath::Max(MaxRevealedDiff, FMath::Max(FMath::Abs(S.Px[I].R - Final.Px[I].R), FMath::Abs(S.Px[I].A - Final.Px[I].A)));
					MaxRevealedDiffAny = FMath::Max(MaxRevealedDiffAny, FMath::Max(MaxRevealedDiff, FMath::Max(FMath::Abs(S.Px[I].G - Final.Px[I].G), FMath::Abs(S.Px[I].B - Final.Px[I].B))));
				}
				if (Prev[I] && !V) ++Removed;
				if (V && !Prev[I])
				{
					++Added;
					Sx += I % S.W;
					Sy += I / S.W;
					if (Map[I] == -2) Map[I] = (int16)T;
				}
				Prev[I] = V;
			}
			Mismatch += StepMismatch;
			if (T == -1) bStartBlank = CountVis(S) == 0;
			if (T == Units - 1) bEndEqual = CountDiff(S, Final) == 0;
			FJson J = Obj();
			J->SetNumberField(TEXT("threshold"), T);
			J->SetNumberField(TEXT("added_px"), Added);
			J->SetNumberField(TEXT("revealed_px_differing_from_final"), StepMismatch);
			if (T >= 0)
			{
				EmptySteps += Added == 0;
				const FVector2D C = Added ? FVector2D(Sx / Added, Sy / Added) : FVector2D(-1, -1);
				J->SetNumberField(TEXT("centroid_x"), C.X);
				J->SetNumberField(TEXT("centroid_y"), C.Y);
				if (Added && PrevC.X >= 0)
				{
					const bool bSameLine = FMath::Abs(C.Y - PrevC.Y) <= 12.0;
					OrderViolations += bSameLine ? !(C.X < PrevC.X) : !(C.Y > PrevC.Y);
				}
				if (Added) PrevC = C;
			}
			if (UnitMapIn && OutVisibleUnits) OutVisibleUnits->Add(VisibleUnits(S, *UnitMapIn, Units));
			Steps.Add(Val(J));
			if (!PngDir.IsEmpty())
			{
				SavePng(S, PngDir / FString::Printf(TEXT("t%03d.png"), T + 1));
				SaveDiffPng(S, Final, PngDir / FString::Printf(TEXT("diff_t%03d.png"), T + 1));
			}
		}
		if (OutUnitMap) *OutUnitMap = Map;
		FJson R = Obj();
		R->SetNumberField(TEXT("units"), Units);
		R->SetNumberField(TEXT("first_final_capture_px_stale"), StaleFirstCapture);
		R->SetBoolField(TEXT("start_blank"), bStartBlank);
		R->SetBoolField(TEXT("end_equals_final"), bEndEqual);
		R->SetNumberField(TEXT("revealed_px_differing_from_final"), Mismatch);
		R->SetNumberField(TEXT("revealed_max_abs_diff_r_or_a"), MaxRevealedDiff);
		R->SetNumberField(TEXT("revealed_max_abs_diff_any_channel"), MaxRevealedDiffAny);
		R->SetNumberField(TEXT("px_removed_between_steps"), Removed);
		R->SetNumberField(TEXT("steps_adding_nothing"), EmptySteps);
		R->SetNumberField(TEXT("desired_size_changes"), DesiredChanged);
		R->SetNumberField(TEXT("reading_order_violations"), OrderViolations);
		R->SetNumberField(TEXT("final_visible_px"), CountVis(Final));
		R->SetBoolField(TEXT("pass"), bStartBlank && bEndEqual && Mismatch == 0 && Removed == 0 && EmptySteps == 0 && DesiredChanged == 0);
		R->SetArrayField(TEXT("steps"), Steps);
		return R;
	}

	// Units whose pixel region (from a unit map) is at least half visible in S; -1 entry means "pixels outside any region".
	static TArray<int32> VisibleUnits(const FShot& S, const TArray<int16>& Map, int32 Units)
	{
		TArray<int32> Total, On;
		Total.Init(0, Units);
		On.Init(0, Units);
		int32 Foreign = 0;
		for (int32 I = 0; I < S.Px.Num(); ++I)
		{
			const int32 U = Map[I];
			const bool V = Vis(S.Px[I]);
			if (U >= 0 && U < Units)
			{
				++Total[U];
				On[U] += V;
			}
			else if (V)
			{
				++Foreign;
			}
		}
		TArray<int32> Out;
		for (int32 U = 0; U < Units; ++U)
			if (Total[U] && On[U] * 2 >= Total[U]) Out.Add(U);
		if (Foreign > 0) Out.Add(-1);
		return Out;
	}

	static bool IsPrefixSet(const TArray<int32>& Set, int32 T)
	{
		if (Set.Num() != T + 1) return false;
		for (int32 I = 0; I <= T; ++I)
			if (Set[I] != I) return false;
		return true;
	}

	// ---------- gates ----------
	void G1G2(int32& OutEnc, int32& OutDec)
	{
		FJson G1 = Obj();
		UMaterialInstanceConstant* MIDebug = MakeMI(TEXT("MI_ArabicReveal_Debug"), FLinearColor::White, 2.f, 0.f); // mode 2: constant white, so pixel = VertexColor
		FinishShaders();
		const FString Word = TEXT("<u0>ااا ممم</>");
		SetThreshold(ThrAll);
		{
			// Probe: is the material output multiplied by the Slate vertex colour, and do MIC/MID parameters apply?
			const FLinearColor Probe(0.1f, 0.5f, 0.9f, 1.f);
			FJsonArr Probes;
			auto ProbeOne = [&](const FString& Name, UMaterialInterface* Mat) {
				UDataTable* DT = NewObject<UDataTable>(GetTransientPackage());
				DT->AddToRoot();
				DT->RowStruct = FRichTextStyleRow::StaticStruct();
				DT->AddRow(TEXT("Default"), Row(Mat, DebugTextSize, Probe));
				DT->AddRow(TEXT("u0"), Row(Mat, DebugTextSize, Probe));
				const FShot S = Draw(MakeText(DT, Word), DebugSize);
				SavePng(S, TEXT("screenshots/G1/probe_") + Name + TEXT(".png"));
				int32 B = 0;
				for (int32 P = 0; P < S.Px.Num(); ++P)
					if (S.Px[P].A > S.Px[B].A) B = P;
				FJson J = Obj();
				J->SetStringField(TEXT("probe"), Name);
				J->SetStringField(TEXT("pixel_at_max_coverage"), S.Px[B].ToString());
				J->SetNumberField(TEXT("visible_px"), CountVis(S));
				Probes.Add(Val(J));
			};
			for (int32 Mode = 0; Mode < 3; ++Mode)
			{
				UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(Material, GetTransientPackage());
				MID->AddToRoot();
				MID->SetScalarParameterValue(TEXT("DebugMode"), Mode);
				MID->SetVectorParameterValue(TEXT("SubtitleColor"), FLinearColor(0.2f, 0.4f, 0.6f, 1.f));
				ProbeOne(FString::Printf(TEXT("MID_DebugMode%d_Color0.2_0.4_0.6"), Mode), MID);
			}
			ProbeOne(TEXT("MIC_Debug_DebugMode1"), MIDebug);
			ProbeOne(TEXT("Parent_M_ArabicReveal"), Material);
			Results->SetArrayField(TEXT("G1_probes"), Probes);
		}

		// G1a: debug mode outputs VertexColor.rgb with opacity 1; compare its alpha mask to the same text without a font material.
		UDataTable* DTDbg = NewObject<UDataTable>(GetTransientPackage(), TEXT("DT_G1"));
		DTDbg->AddToRoot();
		DTDbg->RowStruct = FRichTextStyleRow::StaticStruct();
		const FLinearColor Probe(0.1f, 0.5f, 0.9f, 1.f);
		DTDbg->AddRow(TEXT("Default"), Row(MIDebug, DebugTextSize, Probe));
		DTDbg->AddRow(TEXT("u0"), Row(MIDebug, DebugTextSize, Probe));
		UDataTable* DTPlain = NewObject<UDataTable>(GetTransientPackage(), TEXT("DT_G1_NoMaterial"));
		DTPlain->AddToRoot();
		DTPlain->RowStruct = FRichTextStyleRow::StaticStruct();
		DTPlain->AddRow(TEXT("Default"), Row(nullptr, DebugTextSize, FLinearColor::White));
		DTPlain->AddRow(TEXT("u0"), Row(nullptr, DebugTextSize, FLinearColor::White));
		const FShot SDbg = Draw(MakeText(DTDbg, Word), DebugSize);
		const FShot SPlain = Draw(MakeText(DTPlain, Word), DebugSize);
		SavePng(SDbg, TEXT("screenshots/G1/debug_vertexcolor_0.1_0.5_0.9.png"));
		SavePng(SPlain, TEXT("screenshots/G1/no_material_reference.png"));
		int32 Best = 0, Partial = 0, VisDbg = 0, VisPlain = 0, MaskDiff = 0;
		for (int32 I = 0; I < SDbg.Px.Num(); ++I)
		{
			if (SDbg.Px[I].A > SDbg.Px[Best].A) Best = I;
			Partial += SDbg.Px[I].A > 0.f && SDbg.Px[I].A < 1.f;
			VisDbg += SDbg.Px[I].A > 0.f;
			VisPlain += SPlain.Px[I].A > 0.f;
			MaskDiff += (SDbg.Px[I].A > 0.f) != (SPlain.Px[I].A > 0.f);
		}
		const FLinearColor At = SDbg.Px[Best];
		G1->SetStringField(TEXT("row_color_written"), Probe.ToString());
		G1->SetStringField(TEXT("pixel_at_max_coverage"), At.ToString());
		G1->SetNumberField(TEXT("observed_vc_r"), At.R);
		G1->SetNumberField(TEXT("observed_vc_g"), At.G);
		G1->SetNumberField(TEXT("observed_vc_b"), At.B);
		G1->SetNumberField(TEXT("max_alpha"), At.A);
		G1->SetNumberField(TEXT("visible_px_debug_material"), VisDbg);
		G1->SetNumberField(TEXT("visible_px_no_material"), VisPlain);
		G1->SetNumberField(TEXT("partial_coverage_px"), Partial);
		G1->SetNumberField(TEXT("coverage_mask_px_differing_from_no_material"), MaskDiff);
		G1->SetNumberField(TEXT("canvas_px"), SDbg.Px.Num());

		// G2: sweep 0..255 for two encodings, read VertexColor.R back at full coverage.
		FJson G2 = Obj();
		TArray<TArray<float>> Read;
		for (int32 Enc = 0; Enc < 2; ++Enc)
		{
			TArray<float>& R = Read.AddDefaulted_GetRef();
			FJsonArr Arr;
			for (int32 I = 0; I < 256; ++I)
			{
				UDataTable* DT = NewObject<UDataTable>(GetTransientPackage());
				DT->AddToRoot();
				DT->RowStruct = FRichTextStyleRow::StaticStruct();
				const FLinearColor C(Encode(Enc, I), 0, 0, 1);
				DT->AddRow(TEXT("Default"), Row(MIDebug, DebugTextSize, C));
				DT->AddRow(TEXT("u0"), Row(MIDebug, DebugTextSize, C));
				const FShot S = Draw(MakeText(DT, Word), DebugSize);
				int32 B = 0;
				for (int32 P = 0; P < S.Px.Num(); ++P)
					if (S.Px[P].A > S.Px[B].A) B = P;
				R.Add(S.Px[B].A > 0.f ? S.Px[B].R / S.Px[B].A : -1.f);
				Arr.Add(Num(R.Last()));
			}
			G2->SetArrayField(FString::Printf(TEXT("readback_encoding_%d"), Enc), Arr);
		}
		const TCHAR* EncNames[] = {TEXT("linear i/255"), TEXT("srgb_to_linear(i/255)")};
		const TCHAR* DecNames[] = {TEXT("round(r*255)"), TEXT("round(linear_to_srgb(r)*255)"), TEXT("round(srgb_to_linear(r)*255)")};
		FJsonArr Combos;
		int32 BestCorrect = -1;
		for (int32 Enc = 0; Enc < 2; ++Enc)
			for (int32 Dec = 0; Dec < 3; ++Dec)
			{
				int32 Correct = 0, Contig = -1;
				TSet<int32> Distinct;
				for (int32 I = 0; I < 256; ++I)
				{
					const int32 D = Decode(Dec, Read[Enc][I]);
					Distinct.Add(D);
					Correct += D == I;
					if (D != I && Contig < 0) Contig = I;
				}
				if (Contig < 0) Contig = 256;
				FJson J = Obj();
				J->SetStringField(TEXT("encoding"), EncNames[Enc]);
				J->SetStringField(TEXT("decoding"), DecNames[Dec]);
				J->SetNumberField(TEXT("correct_of_256_bytes"), Correct);
				J->SetNumberField(TEXT("contiguous_from_0"), Contig);
				J->SetNumberField(TEXT("distinct_decoded"), Distinct.Num());
				Combos.Add(Val(J));
				if (Contig > BestCorrect)
				{
					BestCorrect = Contig;
					OutEnc = Enc;
					OutDec = Dec;
				}
			}
		G2->SetArrayField(TEXT("combinations"), Combos);
		G2->SetStringField(TEXT("chosen_encoding"), EncNames[OutEnc]);
		G2->SetStringField(TEXT("chosen_decoding"), DecNames[OutDec]);
		G2->SetNumberField(TEXT("chosen_contiguous_capacity"), BestCorrect);
		Results->SetObjectField(TEXT("G1"), G1);
		Results->SetObjectField(TEXT("G2_sweep"), G2);
	}

	FJson Begin(const FString& OutName)
	{
		World = GEditor->GetEditorWorldContext().World();
		Renderer = MakeUnique<FWidgetRenderer>(false, true);
		OutDir = FPaths::ProjectSavedDir() / OutName;
		IFileManager::Get().DeleteDirectory(*OutDir, false, true);

		FString CorpusText;
		FFileHelper::LoadFileToString(CorpusText, *(FPaths::ProjectDir() / TEXT("TestData/corpus.json")));
		FJson Corpus;
		FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(CorpusText), Corpus);

		FJson Env = Obj();
		Env->SetStringField(TEXT("engine_version"), FEngineVersion::Current().ToString());
		Env->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("none"));
		Env->SetStringField(TEXT("label"), TEXT("UE ISOLATED TEST (UE 5.8.4, NOT 4.27) - NOT DISPATCH"));
		Results->SetObjectField(TEXT("environment"), Env);
		return Corpus;
	}

	void WriteResults()
	{
		FString Out;
		FJsonSerializer::Serialize(Results.ToSharedRef(), TJsonWriterFactory<>::Create(&Out));
		FFileHelper::SaveStringToFile(Out, *(OutDir / TEXT("results.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	}

	void Run()
	{
		FJson Corpus = Begin(TEXT("RevealGate"));

		MakeFont();
		MakeRevealRT();
		MakeMaterial();
		FinishShaders();
		if (Test->HasAnyErrors()) return;

		int32 Enc = 0, Dec = 0;
		G1G2(Enc, Dec);

		UMaterialInstanceConstant* MIFg = MakeMI(TEXT("MI_ArabicReveal_FG"), FLinearColor::White, 0.f, (float)Dec);
		UMaterialInstanceConstant* MIShadow = MakeMI(TEXT("MI_ArabicReveal_Shadow"), FLinearColor(0.3f, 0.7f, 1.f, 1.f), 0.f, (float)Dec);
		UDataTable* DTFg = MakeTable(TEXT("DT_ArabicReveal"), MIFg, TextSize, Enc, true);
		UDataTable* DTShadow = MakeTable(TEXT("DT_ArabicReveal_Shadow"), MIShadow, TextSize, Enc, true);
		FinishShaders();
		const int32 CallsAfterAssets = SetTextCalls;

		// G2 functional: 256 units in one block.
		{
			FString Stress;
			const FString W = Corpus->GetStringField(TEXT("stress_word"));
			const int32 N = (int32)Corpus->GetNumberField(TEXT("stress_units"));
			for (int32 I = 0; I < N; ++I) Stress += W + (I + 1 < N ? TEXT(" ") : TEXT(""));
			int32 Units = 0;
			const FString Markup = BuildMarkup(Stress, Units);
			URichTextBlock* T = MakeText(DTFg, Markup);
			const int32 Before = SetTextCalls;
			FJson R = RevealSequence(T, T, Units, StressSize, TEXT(""), nullptr);
			R->SetNumberField(TEXT("settext_calls_during_reveal"), SetTextCalls - Before);
			SetThreshold(ThrAll);
			SavePng(Draw(T, StressSize), TEXT("screenshots/G2/stress_256_final.png"));
			SetThreshold(127);
			SavePng(Draw(T, StressSize), TEXT("screenshots/G2/stress_256_t127.png"));
			R->RemoveField(TEXT("steps"));
			Results->SetObjectField(TEXT("G2_functional_256"), R);
		}

		// Layout parity: tagged (whitespace units) final vs untagged plain text, plus negative controls (non-whitespace cuts).
		SetThreshold(ThrAll);
		FJsonArr Parity;
		auto ParityCase = [&](const FString& Id, const FString& Plain, const FString& Markup, bool bNegative) {
			URichTextBlock* P = MakeText(DTFg, Plain);
			URichTextBlock* M = MakeText(DTFg, Markup);
			SetThreshold(ThrAll);
			const FShot SP = Draw(P, LineSize);
			const FShot SM = Draw(M, LineSize);
			SavePng(SP, FString::Printf(TEXT("screenshots/parity/%s_plain.png"), *Id));
			SavePng(SM, FString::Printf(TEXT("screenshots/parity/%s_units.png"), *Id));
			FJson J = Obj();
			J->SetStringField(TEXT("id"), Id);
			J->SetBoolField(TEXT("negative_control"), bNegative);
			J->SetStringField(TEXT("markup"), Markup);
			J->SetNumberField(TEXT("px_differing"), CountDiff(SP, SM));
			J->SetNumberField(TEXT("max_abs_channel_diff"), MaxAbsDiff(SP, SM));
			J->SetNumberField(TEXT("visible_px_plain"), CountVis(SP));
			J->SetBoolField(TEXT("identical"), CountDiff(SP, SM) == 0);
			Parity.Add(Val(J));
		};

		FJsonArr Lines;
		for (const TSharedPtr<FJsonValue>& V : Corpus->GetArrayField(TEXT("lines")))
		{
			const FString Id = V->AsObject()->GetStringField(TEXT("id"));
			const FString Text = V->AsObject()->GetStringField(TEXT("text"));
			int32 Units = 0;
			const FString Markup = BuildMarkup(Text, Units);
			ParityCase(Id, Text, Markup, false);

			// G3: foreground (no retainer) and shadow (inside a RetainerBox) share RT_ArabicReveal.
			URichTextBlock* Fg = MakeText(DTFg, Markup);
			URichTextBlock* Sh = MakeText(DTShadow, Markup);
			URetainerBox* Ret = NewObject<URetainerBox>(GetTransientPackage());
			Ret->AddToRoot();
			Ret->AddChild(Sh);
			const int32 Before = SetTextCalls, BeforeStyle = SetStyleCalls;
			TArray<int16> Map;
			FJson J = Obj();
			J->SetStringField(TEXT("id"), Id);
			J->SetStringField(TEXT("markup"), Markup);
			J->SetObjectField(TEXT("foreground"), RevealSequence(Fg, Fg, Units, LineSize, TEXT("screenshots/lines/") + Id + TEXT("/fg"), &Map));
			TArray<TArray<int32>> FgUnits, ShUnits;
			RevealSequence(Fg, Fg, Units, LineSize, TEXT(""), nullptr, &FgUnits, &Map);
			FJson ShR = RevealSequence(Ret, Sh, Units, LineSize, TEXT("screenshots/lines/") + Id + TEXT("/shadow_retainer"), nullptr, &ShUnits, &Map,
				[Ret]() { Ret->RequestRender(); });
			ShR->RemoveField(TEXT("steps"));
			J->SetObjectField(TEXT("shadow_retainer_requestrender"), ShR);
			int32 SyncMismatch = 0, NotPrefix = 0;
			for (int32 S = 0; S < FgUnits.Num(); ++S)
			{
				SyncMismatch += FgUnits[S] != ShUnits[S];
				NotPrefix += !IsPrefixSet(FgUnits[S], S - 1);
			}
			J->SetNumberField(TEXT("steps_fg_shadow_visible_units_differ"), SyncMismatch);
			J->SetNumberField(TEXT("steps_fg_not_exact_prefix"), NotPrefix);
			J->SetNumberField(TEXT("settext_calls_during_reveal"), SetTextCalls - Before);
			J->SetNumberField(TEXT("settextstyleset_calls_during_reveal"), SetStyleCalls - BeforeStyle);
			Lines.Add(Val(J));

			// Retainer policy: does a threshold change show up without RequestRender? (3 frames per step)
			if (Id == TEXT("long_wrap") || Id == TEXT("speaker"))
			{
				FJson RJ = Obj();
				for (int32 Mode = 0; Mode < 3; ++Mode)
				{
					// 0: RenderOnInvalidation=true, no RequestRender; 1: same + RequestRender; 2: RenderOnInvalidation=false (every paint)
					URichTextBlock* S2 = MakeText(DTShadow, Markup);
					URetainerBox* R2 = NewObject<URetainerBox>(GetTransientPackage());
					R2->AddToRoot();
					FindFProperty<FBoolProperty>(URetainerBox::StaticClass(), TEXT("RenderOnInvalidation"))->SetPropertyValue_InContainer(R2, Mode != 2);
					R2->AddChild(S2);
					SetThreshold(-1);
					Draw(R2, LineSize);
					FJsonArr Lag;
					int32 Stale = 0;
					for (int32 T = 0; T < Units; ++T)
					{
						SetThreshold(T);
						if (Mode == 1) R2->RequestRender();
						int32 First = -1;
						for (int32 F = 0; F < 3; ++F)
						{
							const bool Ok = VisibleUnits(Draw(R2, LineSize), Map, Units) == FgUnits[T + 1];
							if (Ok && First < 0) First = F;
						}
						Stale += First != 0;
						Lag.Add(Num(First));
					}
					FJson MJ = Obj();
					MJ->SetArrayField(TEXT("first_correct_frame_per_step"), Lag);
					MJ->SetNumberField(TEXT("stale_steps"), Stale);
					RJ->SetObjectField(Mode == 0 ? TEXT("on_invalidation_no_requestrender") : Mode == 1 ? TEXT("on_invalidation_requestrender") : TEXT("render_every_paint"), MJ);
				}
				Results->SetObjectField(TEXT("G3_retainer_policy_") + Id, RJ);
			}

			// G5 parent tint / opacity (speaker line only)
			if (Id == TEXT("speaker"))
			{
				FJson TJ = Obj();
				for (int32 Mode = 0; Mode < 2; ++Mode)
				{
					URichTextBlock* T2 = MakeText(DTFg, Markup);
					UBorder* B = NewObject<UBorder>(GetTransientPackage());
					B->AddToRoot();
					B->SetPadding(FMargin(0));
					B->SetBrushColor(FLinearColor::Transparent);
					if (Mode == 0) B->SetContentColorAndOpacity(FLinearColor(0.5f, 0.5f, 0.5f, 1.f));
					else B->SetRenderOpacity(0.5f);
					B->SetContent(T2);
					int32 Wrong = 0;
					for (int32 T = -1; T < Units; ++T)
					{
						SetThreshold(T);
						Wrong += VisibleUnits(Draw(B, LineSize), Map, Units) != FgUnits[T + 1];
					}
					SetThreshold(0);
					SetThreshold(ThrAll);
					const FShot PS = Draw(B, LineSize);
					SavePng(PS, FString::Printf(TEXT("screenshots/G5/parent_%s_final.png"), Mode == 0 ? TEXT("rgb_tint_0.5") : TEXT("render_opacity_0.5")));
					FLinearColor MaxC(0, 0, 0, 0);
					for (const FLinearColor& Px : PS.Px) MaxC = FLinearColor(FMath::Max(MaxC.R, Px.R), FMath::Max(MaxC.G, Px.G), FMath::Max(MaxC.B, Px.B), FMath::Max(MaxC.A, Px.A));
					TJ->SetStringField(Mode == 0 ? TEXT("rgb_tint_0.5_max_pixel") : TEXT("render_opacity_0.5_max_pixel"), MaxC.ToString());
					TJ->SetNumberField(Mode == 0 ? TEXT("rgb_tint_0.5_wrong_steps") : TEXT("render_opacity_0.5_wrong_steps"), Wrong);
				}
				TJ->SetNumberField(TEXT("steps"), Units + 1);
				Results->SetObjectField(TEXT("G5_parent"), TJ);
			}
		}
		for (const TSharedPtr<FJsonValue>& V : Corpus->GetArrayField(TEXT("negative_controls")))
			ParityCase(V->AsObject()->GetStringField(TEXT("id")), V->AsObject()->GetStringField(TEXT("plain")), V->AsObject()->GetStringField(TEXT("markup")), true);
		Results->SetArrayField(TEXT("G3_lines"), Lines);
		Results->SetArrayField(TEXT("layout_parity"), Parity);

		G5Pool(DTFg, DTShadow);
		Culture();
		Results->SetNumberField(TEXT("first_paints"), FirstPaints);
		Results->SetNumberField(TEXT("first_paints_differing_from_second"), FirstPaintsDiffering);
		Results->SetNumberField(TEXT("first_paints_empty_then_visible"), FirstPaintsEmptyThenNot);
		Results->SetNumberField(TEXT("settext_calls_total"), SetTextCalls);
		Results->SetNumberField(TEXT("settext_calls_after_assets"), SetTextCalls - CallsAfterAssets);
		WriteResults();
	}

	// R8 (round 008): per-block threshold in VertexColor.G from a Border tint; no render target, no ClearRenderTarget2D.
	// Same checks as G2/G3/G5 plus a G-byte sweep, an outline layer and two blocks revealing different thresholds at once.
	void RunTint(bool bPrinting = false)
	{
		Scheme = bPrinting ? 1 : 0;
		FJson Corpus = Begin(bPrinting ? TEXT("RevealGateTintB") : TEXT("RevealGateTint"));
		PackageRoot = bPrinting ? TEXT("/Game/ArabicRevealTintB") : TEXT("/Game/ArabicRevealTint");
		MakeFont();
		MakeMaterial(TEXT("M_ArabicRevealTint"), bPrinting ? RevealPrintingHlsl : RevealTintHlsl, false);
		FinishShaders();
		if (Test->HasAnyErrors()) return;
		UMaterialInstanceConstant* MIDebug = MakeMI(TEXT("MI_ArabicRevealTint_Debug"), FLinearColor::White, 2.f, 1.f); // pixel = VertexColor
		UMaterialInstanceConstant* MIFg = MakeMI(TEXT("MI_ArabicRevealTint_FG"), FLinearColor::White, 0.f, 1.f);
		UMaterialInstanceConstant* MIShadow = MakeMI(TEXT("MI_ArabicRevealTint_Shadow"), FLinearColor(0.3f, 0.7f, 1.f, 1.f), 0.f, 1.f);
		UMaterialInstanceConstant* MIOutline = MakeMI(TEXT("MI_ArabicRevealTint_Outline"), FLinearColor::Black, 0.f, 1.f);
		UDataTable* DTFg = MakeTable(TEXT("DT_ArabicRevealTint"), MIFg, TextSize, 1, true);
		UDataTable* DTShadow = MakeTable(TEXT("DT_ArabicRevealTint_Shadow"), MIShadow, TextSize, 1, true);
		UDataTable* DTOutline = MakeTable(TEXT("DT_ArabicRevealTint_Outline"), MIFg, TextSize, 1, true, MIOutline);
		FinishShaders();
		const int32 CallsAfterAssets = SetTextCalls;
		bool bAll = true;

		// G-byte sweep through the tint path; R must stay at the row's byte 1 throughout.
		if (!bPrinting)
		{
			UDataTable* DT = NewObject<UDataTable>(GetTransientPackage());
			DT->AddToRoot();
			DT->RowStruct = FRichTextStyleRow::StaticStruct();
			DT->AddRow(TEXT("Default"), Row(MIDebug, DebugTextSize, FLinearColor(Encode(1, 1), 1, 1, 1)));
			DT->AddRow(TEXT("u0"), Row(MIDebug, DebugTextSize, FLinearColor(Encode(1, 1), 1, 1, 1)));
			UBorder* B = MakeTintBorder(MakeText(DT, TEXT("<u0>ااا ممم</>")));
			int32 GOk = 0, ROk = 0;
			FJsonArr Arr;
			for (int32 I = 0; I < 256; ++I)
			{
				B->SetContentColorAndOpacity(FLinearColor(1.f, Encode(1, I), 1.f, 1.f));
				const FShot S = Draw(B, DebugSize);
				int32 Best = 0;
				for (int32 P = 0; P < S.Px.Num(); ++P)
					if (S.Px[P].A > S.Px[Best].A) Best = P;
				const FLinearColor C = S.Px[Best];
				GOk += C.A > 0.f && Decode(1, C.G / C.A) == I;
				ROk += C.A > 0.f && Decode(1, C.R / C.A) == 1;
				Arr.Add(Num(C.A > 0.f ? C.G / C.A : -1.f));
			}
			FJson J = Obj();
			J->SetNumberField(TEXT("g_bytes_decoded_correctly_of_256"), GOk);
			J->SetNumberField(TEXT("r_index_unchanged_of_256"), ROk);
			J->SetArrayField(TEXT("readback_g"), Arr);
			Results->SetObjectField(TEXT("R8_sweep_g"), J);
			bAll &= GOk == 256 && ROk == 256;
		}

		FJsonArr Lines;
		for (const TSharedPtr<FJsonValue>& V : Corpus->GetArrayField(TEXT("lines")))
		{
			const FString Id = V->AsObject()->GetStringField(TEXT("id"));
			const FString Text = V->AsObject()->GetStringField(TEXT("text"));
			int32 Units = 0;
			const FString Markup = BuildMarkup(Text, Units);
			URichTextBlock* Fg = MakeText(DTFg, Markup);
			URichTextBlock* Sh = MakeText(DTShadow, Markup);
			URichTextBlock* Ol = MakeText(DTOutline, Markup);
			UBorder* FgB = MakeTintBorder(Fg);
			UBorder* ShB = MakeTintBorder(Sh);
			UBorder* OlB = MakeTintBorder(Ol);
			URetainerBox* Ret = NewObject<URetainerBox>(GetTransientPackage());
			Ret->AddToRoot();
			Ret->AddChild(ShB); // the threshold Border is inside the retainer, so the retained image itself is never tinted
			ThresholdOverride = [FgB, ShB, OlB](float T) {
				FgB->SetContentColorAndOpacity(TintFor(T));
				ShB->SetContentColorAndOpacity(TintFor(T));
				OlB->SetContentColorAndOpacity(TintFor(T));
			};
			const int32 Before = SetTextCalls, BeforeStyle = SetStyleCalls;
			TArray<int16> Map, OlMap;
			TArray<TArray<int32>> FgUnits, ShUnits;
			FJson J = Obj();
			J->SetStringField(TEXT("id"), Id);
			J->SetStringField(TEXT("markup"), Markup);
			FJson FgR = RevealSequence(FgB, Fg, Units, LineSize, TEXT("screenshots/lines/") + Id + TEXT("/fg"), &Map);
			RevealSequence(FgB, Fg, Units, LineSize, TEXT(""), nullptr, &FgUnits, &Map);
			FJson ShR = RevealSequence(Ret, Sh, Units, LineSize, TEXT("screenshots/lines/") + Id + TEXT("/shadow_retainer"), nullptr, &ShUnits, &Map,
				[Ret]() { Ret->RequestRender(); });
			FJson OlR = RevealSequence(OlB, Ol, Units, LineSize, TEXT("screenshots/lines/") + Id + TEXT("/outline"), &OlMap);
			int32 SyncMismatch = 0;
			for (int32 S = 0; S < FgUnits.Num(); ++S) SyncMismatch += FgUnits[S] != ShUnits[S];

			// Full reveal vs the same text without unit tags (one Default run): layout must be identical.
			URichTextBlock* P = MakeText(DTFg, Text);
			UBorder* PB = MakeTintBorder(P);
			PB->SetContentColorAndOpacity(TintFor(ThrAll));
			SetThreshold(ThrAll);
			const FShot SP = Draw(PB, LineSize), SM = Draw(FgB, LineSize), SO = Draw(OlB, LineSize);
			// Outline layer must add dark outline pixels around the fill.
			int32 OutlinePx = 0;
			for (int32 I = 0; I < SO.Px.Num(); ++I) OutlinePx += SO.Px[I].A > 0.5f && SO.Px[I].R < 0.25f * SO.Px[I].A && !Vis(SM.Px[I]);

			for (FJson* R : {&FgR, &ShR, &OlR}) (*R)->RemoveField(TEXT("steps"));
			J->SetObjectField(TEXT("foreground"), FgR);
			J->SetObjectField(TEXT("shadow_retainer_requestrender"), ShR);
			J->SetObjectField(TEXT("outline"), OlR);
			J->SetNumberField(TEXT("steps_fg_shadow_visible_units_differ"), SyncMismatch);
			J->SetNumberField(TEXT("full_reveal_px_differing_from_untagged_text"), CountDiff(SP, SM));
			J->SetNumberField(TEXT("full_reveal_max_abs_diff_from_untagged_text"), MaxAbsDiff(SP, SM));
			J->SetNumberField(TEXT("outline_only_dark_px"), OutlinePx);
			J->SetNumberField(TEXT("settext_calls_during_reveal"), SetTextCalls - Before - 1); // -1: the untagged reference text
			J->SetNumberField(TEXT("settextstyleset_calls_during_reveal"), SetStyleCalls - BeforeStyle - 1);
			// The G-channel compensation Col.g / VC.g * VC.g can round by one float ULP as the threshold changes, so revealed
			// pixels may differ from the final by <= 1e-6 (identical once written to 8 bits). Everything else stays exact.
			auto Ok = [](const FJson& R) {
				return R->GetBoolField(TEXT("start_blank")) && R->GetBoolField(TEXT("end_equals_final")) && R->GetNumberField(TEXT("px_removed_between_steps")) == 0 &&
					R->GetNumberField(TEXT("steps_adding_nothing")) == 0 && R->GetNumberField(TEXT("desired_size_changes")) == 0 &&
					R->GetNumberField(TEXT("revealed_max_abs_diff_any_channel")) <= 1e-6;
			};
			const bool bPass = Ok(FgR) && Ok(ShR) && Ok(OlR) &&
				FgR->GetNumberField(TEXT("reading_order_violations")) == 0 && SyncMismatch == 0 && OutlinePx > 0 && SetTextCalls - Before - 1 == 0;
			J->SetBoolField(TEXT("pass_within_1e-6"), bPass);
			J->SetBoolField(TEXT("pass_bit_exact"), bPass && FgR->GetBoolField(TEXT("pass")) && ShR->GetBoolField(TEXT("pass")) && OlR->GetBoolField(TEXT("pass")));
			bAll &= bPass;
			Lines.Add(Val(J));

			// Informational: does the retainer pick up a tint change without RequestRender? (all paints happen in one engine frame here)
			if (Id == TEXT("long_wrap") || Id == TEXT("speaker"))
			{
				int32 Stale = 0;
				for (int32 T = 0; T < Units; ++T)
				{
					SetThreshold(T);
					Stale += VisibleUnits(Draw(Ret, LineSize), Map, Units) != FgUnits[T + 1];
				}
				Results->SetNumberField(TEXT("R8_retainer_no_requestrender_stale_steps_") + Id, Stale);
			}
		}
		Results->SetArrayField(TEXT("R8_lines"), Lines);

		// Two blocks in one VerticalBox, each with its own threshold Border, revealed independently in the same paint.
		{
			TMap<FString, FString> ById;
			for (const TSharedPtr<FJsonValue>& V : Corpus->GetArrayField(TEXT("lines")))
				ById.Add(V->AsObject()->GetStringField(TEXT("id")), V->AsObject()->GetStringField(TEXT("text")));
			int32 UA = 0, UB = 0;
			URichTextBlock* TA = MakeText(DTFg, BuildMarkup(ById[TEXT("multiline")], UA));
			URichTextBlock* TB = MakeText(DTFg, BuildMarkup(ById[TEXT("punctuation")], UB));
			UBorder* BA = MakeTintBorder(TA);
			UBorder* BB = MakeTintBorder(TB);
			UVerticalBox* Box = NewObject<UVerticalBox>(GetTransientPackage());
			Box->AddToRoot();
			Box->AddChildToVerticalBox(BA);
			Box->AddChildToVerticalBox(BB);
			const FIntPoint Size(1000, 400);
			TArray<int16> MapA, MapB;
			ThresholdOverride = [BA, BB](float T) { BA->SetContentColorAndOpacity(TintFor(T)); BB->SetContentColorAndOpacity(TintFor(-1)); };
			FJson RA = RevealSequence(Box, TA, UA, Size, TEXT(""), &MapA);
			ThresholdOverride = [BA, BB](float T) { BA->SetContentColorAndOpacity(TintFor(-1)); BB->SetContentColorAndOpacity(TintFor(T)); };
			FJson RB = RevealSequence(Box, TB, UB, Size, TEXT(""), &MapB);
			ThresholdOverride = nullptr;
			BA->SetContentColorAndOpacity(TintFor(ThrAll));
			BB->SetContentColorAndOpacity(TintFor(ThrAll));
			const FShot Both = Draw(Box, Size);
			FJsonArr Cases;
			int32 Bad = 0;
			for (const FIntPoint& C : {FIntPoint(1, 3), FIntPoint(4, 0), FIntPoint(-1, 6), FIntPoint(UA - 1, -1), FIntPoint(2, 2)})
			{
				BA->SetContentColorAndOpacity(TintFor(C.X));
				BB->SetContentColorAndOpacity(TintFor(C.Y));
				const FShot S = Draw(Box, Size);
				SavePng(S, FString::Printf(TEXT("screenshots/concurrent/a%d_b%d.png"), C.X, C.Y));
				int32 Wrong = 0;
				for (int32 I = 0; I < S.Px.Num(); ++I)
				{
					// pixel I is lit iff the unit that first lit it in its own block's solo sequence is <= that block's threshold
					const bool bExpect = (MapA[I] >= 0 && MapA[I] <= C.X) || (MapB[I] >= 0 && MapB[I] <= C.Y);
					Wrong += Vis(S.Px[I]) != bExpect || (bExpect && !(S.Px[I] == Both.Px[I]));
				}
				Bad += Wrong;
				FJson J = Obj();
				J->SetNumberField(TEXT("threshold_a"), C.X);
				J->SetNumberField(TEXT("threshold_b"), C.Y);
				J->SetNumberField(TEXT("px_wrong"), Wrong);
				Cases.Add(Val(J));
			}
			FJson J = Obj();
			J->SetBoolField(TEXT("solo_a_pass"), RA->GetBoolField(TEXT("pass")));
			J->SetBoolField(TEXT("solo_b_pass"), RB->GetBoolField(TEXT("pass")));
			J->SetArrayField(TEXT("cases"), Cases);
			J->SetBoolField(TEXT("pass"), Bad == 0 && RA->GetBoolField(TEXT("pass")) && RB->GetBoolField(TEXT("pass")));
			Results->SetObjectField(TEXT("R8_concurrent_blocks"), J);
			bAll &= J->GetBoolField(TEXT("pass"));
		}

		// Per-block subtitle colour without touching the vertex colour: the white fill is retained by its own RetainerBox whose
		// per-instance effect MID (stock GetEffectMaterial) multiplies the retained image by SubtitleColor.
		if (!bPrinting)
		{
			UMaterial* M = NewAsset<UMaterial>(TEXT("M_ArabicColorize"));
			M->MaterialDomain = MD_UI;
			M->BlendMode = BLEND_Translucent;
			M->SetShadingModel(MSM_Unlit);
			auto* Tex = NewObject<UMaterialExpressionTextureSampleParameter2D>(M);
			Tex->ParameterName = TEXT("Texture"); // URetainerBox's default TextureParameter
			Tex->Texture = LoadObject<UTexture2D>(nullptr, TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"));
			Tex->SamplerType = SAMPLERTYPE_Color;
			auto* Col = NewObject<UMaterialExpressionVectorParameter>(M);
			Col->ParameterName = TEXT("SubtitleColor");
			Col->DefaultValue = FLinearColor::White;
			auto* Mul = NewObject<UMaterialExpressionMultiply>(M);
			Mul->A.Connect(0, Tex); // RGB
			Mul->B.Connect(0, Col);
			for (UMaterialExpression* E : TArray<UMaterialExpression*>{Tex, Col, Mul})
			{
				E->Material = M;
				M->GetExpressionCollection().AddExpression(E);
			}
			M->GetEditorOnlyData()->EmissiveColor.Connect(0, Mul);
			M->GetEditorOnlyData()->Opacity.Connect(4, Tex); // A
			M->PreEditChange(nullptr);
			M->PostEditChange();
			FinishShaders();
			if (const FMaterialResource* Res = M->GetMaterialResource(GMaxRHIShaderPlatform))
				for (const FString& E : Res->GetCompileErrors()) Test->AddError(TEXT("M_ArabicColorize compile: ") + E);
			Save(M);

			const FLinearColor C(0.9f, 0.35f, 0.2f, 1.f);
			UMaterialInstanceConstant* MIColored = MakeMI(TEXT("MI_ArabicRevealTint_Colored"), C, 0.f, 1.f);
			UDataTable* DTColored = MakeTable(TEXT("DT_ArabicRevealTint_Colored"), MIColored, TextSize, 1, false);
			FinishShaders();
			FJsonArr Arr;
			bool bPass = true;
			for (const TSharedPtr<FJsonValue>& V : Corpus->GetArrayField(TEXT("lines")))
			{
				const FString Id = V->AsObject()->GetStringField(TEXT("id"));
				if (Id != TEXT("speaker") && Id != TEXT("long_wrap") && Id != TEXT("mixed_test42")) continue;
				int32 Units = 0;
				const FString Markup = BuildMarkup(V->AsObject()->GetStringField(TEXT("text")), Units);
				URichTextBlock* T = MakeText(DTFg, Markup);
				UBorder* B = MakeTintBorder(T);
				URetainerBox* R = NewObject<URetainerBox>(GetTransientPackage());
				R->AddToRoot();
				R->SetEffectMaterial(M);
				R->AddChild(B);
				R->TakeWidget(); // the effect MID exists once the Slate widget does
				UMaterialInstanceDynamic* MID = R->GetEffectMaterial();
				if (MID) MID->SetVectorParameterValue(TEXT("SubtitleColor"), C);
				ThresholdOverride = [B](float Thr) { B->SetContentColorAndOpacity(TintFor(Thr)); };
				FJson Seq = RevealSequence(R, T, Units, LineSize, TEXT("screenshots/colorize/") + Id, nullptr, nullptr, nullptr, [R]() { R->RequestRender(); });
				Seq->RemoveField(TEXT("steps"));
				// Reference: the same line drawn directly with a coloured font material (what a per-block MID would give).
				UBorder* BD = MakeTintBorder(MakeText(DTColored, Markup));
				BD->SetContentColorAndOpacity(TintFor(ThrAll));
				SetThreshold(ThrAll);
				R->RequestRender();
				const FShot SR = Draw(R, LineSize), SD = Draw(BD, LineSize);
				int32 BR = 0, BDx = 0;
				for (int32 I = 0; I < SR.Px.Num(); ++I)
				{
					if (SR.Px[I].A > SR.Px[BR].A) BR = I;
					if (SD.Px[I].A > SD.Px[BDx].A) BDx = I;
				}
				const FLinearColor PR = SR.Px[BR], PD = SD.Px[BDx];
				const float ColErr = FMath::Max3(FMath::Abs(PR.R - C.R), FMath::Abs(PR.G - C.G), FMath::Abs(PR.B - C.B));
				const bool bOk = MID && Seq->GetBoolField(TEXT("start_blank")) && Seq->GetBoolField(TEXT("end_equals_final")) &&
					Seq->GetNumberField(TEXT("px_removed_between_steps")) == 0 && Seq->GetNumberField(TEXT("steps_adding_nothing")) == 0 &&
					Seq->GetNumberField(TEXT("revealed_px_differing_from_final")) == 0 && ColErr <= 1.5f / 255.f && CountVis(SR) == CountVis(SD);
				bPass &= bOk;
				FJson J = Obj();
				J->SetStringField(TEXT("id"), Id);
				J->SetBoolField(TEXT("effect_mid_created"), MID != nullptr);
				J->SetObjectField(TEXT("reveal"), Seq);
				J->SetStringField(TEXT("retained_colorized_full_coverage_px"), PR.ToString());
				J->SetStringField(TEXT("direct_colored_material_full_coverage_px"), PD.ToString());
				J->SetNumberField(TEXT("full_coverage_color_error"), ColErr);
				J->SetNumberField(TEXT("visible_px_retained"), CountVis(SR));
				J->SetNumberField(TEXT("visible_px_direct"), CountVis(SD));
				J->SetNumberField(TEXT("px_differing_retained_vs_direct"), CountDiff(SR, SD));
				J->SetNumberField(TEXT("max_abs_diff_retained_vs_direct"), MaxAbsDiff(SR, SD));
				J->SetBoolField(TEXT("pass"), bOk);
				SavePng(SD, TEXT("screenshots/colorize/") + Id + TEXT("/direct_colored_reference.png"));
				Arr.Add(Val(J));
			}
			FJson J = Obj();
			J->SetStringField(TEXT("color"), C.ToString());
			J->SetArrayField(TEXT("lines"), Arr);
			J->SetBoolField(TEXT("pass"), bPass);
			Results->SetObjectField(TEXT("R8_colorize"), J);
			bAll &= bPass;
			ThresholdOverride = nullptr;
		}

		G5Pool(DTFg, DTShadow, TEXT("R8_pool"), true);
		ThresholdOverride = nullptr;
		bAll &= Results->GetObjectField(TEXT("R8_pool"))->GetBoolField(TEXT("pass"));
		Results->SetNumberField(TEXT("first_paints"), FirstPaints);
		Results->SetNumberField(TEXT("first_paints_empty_then_visible"), FirstPaintsEmptyThenNot);
		Results->SetNumberField(TEXT("settext_calls_after_assets"), SetTextCalls - CallsAfterAssets);
		Results->SetStringField(TEXT("scheme"), bPrinting ? TEXT("R8b: M_SubtitlePrinting mirror, B = K^(t-i), K=10.5, max 37 units") : TEXT("R8: custom material, index R / threshold G"));
		Results->SetBoolField(TEXT("R8_all_pass"), bAll);
		WriteResults();
	}

	// Pooled block model: one fg+shadow pair and one threshold RT reused for lines A, B, C.
	// SetText happens only at "Set Displayed Line"; skip/finish/reset/stop only write the threshold.
	// bTint (R8): each text sits in its own threshold Border; the shadow Border is inside the retainer.
	void G5Pool(UDataTable* DTFg, UDataTable* DTShadow, const FString& ResultKey = TEXT("G5_pool"), bool bTint = false)
	{
		const FString A = TEXT("السطر الأول من الحوار هنا"), B = TEXT("مرحبا TEST-42 بالعالم"), C = TEXT("لا إله إلا الله");
		const FString PngPrefix = bTint ? TEXT("screenshots/pool_") : TEXT("screenshots/G5/pool_");
		URichTextBlock* Fg = MakeText(DTFg, TEXT(""));
		URichTextBlock* Sh = MakeText(DTShadow, TEXT(""));
		UWidget* FgRoot = Fg;
		UWidget* ShRoot = Sh;
		if (bTint)
		{
			UBorder* FB = MakeTintBorder(Fg);
			UBorder* SB = MakeTintBorder(Sh);
			FgRoot = FB;
			ShRoot = SB;
			ThresholdOverride = [FB, SB](float T) {
				FB->SetContentColorAndOpacity(TintFor(T));
				SB->SetContentColorAndOpacity(TintFor(T));
			};
		}
		URetainerBox* Ret = NewObject<URetainerBox>(GetTransientPackage());
		Ret->AddToRoot();
		Ret->AddChild(ShRoot);
		FJsonArr Log;
		int32 Fail = 0;
		auto SetLine = [&](const FString& Text, int32& Units) {
			SetThreshold(-1); // reset before the new text becomes visible
			const FString M = BuildMarkup(Text, Units);
			Fg->SetText(FText::FromString(M));
			Sh->SetText(FText::FromString(M));
			SetTextCalls += 2;
			Ret->RequestRender();
		};
		// reference finals per line from fresh widgets
		auto Ref = [&](const FString& Text) {
			int32 U = 0;
			UWidget* R = MakeText(DTFg, BuildMarkup(Text, U));
			if (bTint)
			{
				UBorder* RB = MakeTintBorder(R); // R8b needs the Border: without it only unit 0 shows
				RB->SetContentColorAndOpacity(TintFor(ThrAll));
				R = RB;
			}
			SetThreshold(ThrAll);
			return Draw(R, LineSize);
		};
		const FShot RefA = Ref(A), RefB = Ref(B), RefC = Ref(C);
		auto Check = [&](const FString& Step, float Thr, const FShot* RefFinal, bool bExpectBlank, bool bExpectFull) {
			SetThreshold(Thr);
			Ret->RequestRender();
			const FShot S = Draw(FgRoot, LineSize);
			const FShot SS = Draw(Ret, LineSize);
			int32 NotInRef = 0;
			for (int32 I = 0; I < S.Px.Num(); ++I) NotInRef += Vis(S.Px[I]) && !(RefFinal && S.Px[I] == RefFinal->Px[I]);
			const int32 VisFg = CountVis(S), VisSh = CountVis(SS);
			bool Ok = NotInRef == 0;
			if (bExpectBlank) Ok &= VisFg == 0 && VisSh == 0;
			if (bExpectFull) Ok &= RefFinal && CountDiff(S, *RefFinal) == 0;
			if (!bExpectBlank) Ok &= VisFg > 0 && VisSh > 0;
			Fail += !Ok;
			SavePng(S, PngPrefix + Step + TEXT(".png"));
			FJson J = Obj();
			J->SetStringField(TEXT("step"), Step);
			J->SetNumberField(TEXT("threshold"), Thr);
			J->SetNumberField(TEXT("fg_visible_px"), VisFg);
			J->SetNumberField(TEXT("shadow_visible_px"), VisSh);
			J->SetNumberField(TEXT("fg_px_not_in_current_line_final"), NotInRef);
			J->SetBoolField(TEXT("ok"), Ok);
			Log.Add(Val(J));
		};
		int32 UA = 0, UB = 0, UC = 0;
		SetLine(A, UA);
		Check(TEXT("A_set"), -1, &RefA, true, false);
		Check(TEXT("A_reveal_t1"), 1, &RefA, false, false);
		Check(TEXT("A_skip"), UA - 1, &RefA, false, true);
		Check(TEXT("A_finish"), UA - 1, &RefA, false, true);
		Check(TEXT("A_reset"), -1, &RefA, true, false);
		SetLine(B, UB);
		Check(TEXT("B_set"), -1, &RefB, true, false);
		Check(TEXT("B_reveal_t1"), 1, &RefB, false, false);
		Check(TEXT("B_reset"), -1, &RefB, true, false);
		SetLine(C, UC);
		Check(TEXT("C_reveal_t0"), 0, &RefC, false, false);
		Check(TEXT("C_finish"), UC - 1, &RefC, false, true);
		Check(TEXT("C_stop_displaying_line"), -1, &RefC, true, false);
		FJson R = Obj();
		R->SetArrayField(TEXT("log"), Log);
		R->SetNumberField(TEXT("failed_checks"), Fail);
		R->SetBoolField(TEXT("pass"), Fail == 0);
		Results->SetObjectField(ResultKey, R);
	}

	void Culture()
	{
		FJsonArr Arr;
		const FString Orig = UKismetInternationalizationLibrary::GetCurrentCulture();
		for (const TCHAR* C : {TEXT("ar"), TEXT("ar-SA"), TEXT("en"), TEXT("en-US")})
		{
			FJson J = Obj();
			J->SetStringField(TEXT("requested"), C);
			J->SetBoolField(TEXT("set_ok"), UKismetInternationalizationLibrary::SetCurrentCulture(C, false));
			J->SetStringField(TEXT("GetCurrentLanguage"), UKismetInternationalizationLibrary::GetCurrentLanguage());
			J->SetStringField(TEXT("GetCurrentCulture"), UKismetInternationalizationLibrary::GetCurrentCulture());
			J->SetStringField(TEXT("GetCurrentLocale"), UKismetInternationalizationLibrary::GetCurrentLocale());
			J->SetBoolField(TEXT("language_starts_with_ar"), UKismetInternationalizationLibrary::GetCurrentLanguage().StartsWith(TEXT("ar")));
			Arr.Add(Val(J));
		}
		UKismetInternationalizationLibrary::SetCurrentCulture(Orig, false);
		FJson R = Obj();
		R->SetStringField(TEXT("original_culture"), Orig);
		R->SetStringField(TEXT("command_line"), FCommandLine::Get());
		R->SetArrayField(TEXT("cases"), Arr);
		Results->SetObjectField(TEXT("culture"), R);
	}
};
} // namespace RevealGate

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRevealGateAll, "RevealGate.All", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRevealGateAll::RunTest(const FString& Parameters)
{
	RevealGate::FHarness H;
	H.Test = this;
	H.Run();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRevealGateTint, "RevealGate.Tint", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRevealGateTint::RunTest(const FString& Parameters)
{
	RevealGate::FHarness H;
	H.Test = this;
	H.RunTint();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRevealGateTintB, "RevealGate.TintB", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRevealGateTintB::RunTest(const FString& Parameters)
{
	RevealGate::FHarness H;
	H.Test = this;
	H.RunTint(true);
	RevealGate::Scheme = 0;
	return true;
}

// Culture-only probe for a -culture=<x> launch.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRevealGateCulture, "RevealGate.Culture", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRevealGateCulture::RunTest(const FString& Parameters)
{
	FString Requested;
	FParse::Value(FCommandLine::Get(), TEXT("culture="), Requested);
	UE_LOG(LogTemp, Display, TEXT("REVEALGATE_CULTURE requested=%s language=%s culture=%s locale=%s"), *Requested,
		*UKismetInternationalizationLibrary::GetCurrentLanguage(),
		*UKismetInternationalizationLibrary::GetCurrentCulture(), *UKismetInternationalizationLibrary::GetCurrentLocale());
	return true;
}
#endif
