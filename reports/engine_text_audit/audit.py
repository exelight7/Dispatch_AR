"""Read-only inventory of the packaged English engine text resource."""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json,re
from scripts.localization import read_locres

root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent
source=root/'extracted/Engine/Content/Localization/Engine/en/Engine.locres'
raw=source.read_bytes()
rows=read_locres(raw)['rows']
counts=Counter(r['namespace'] for r in rows)
distribution=[{'namespace':n,'count':c} for n,c in sorted(counts.items(),key=lambda pair:(-pair[1],pair[0]))]
(out/'namespace_distribution.json').write_text(json.dumps(distribution,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

native_full={'NetworkErrors','GameViewportClient','WindowsDynamicRHI','D3D11RHI','D3D12RHI','Launch','EngineInit','EngineLoop'}
engine_keys={
 'UsedCheatCommands','FailedToLoadDefaultMap','NetworkDriverInit','NetworkInit',
 'PendingNetGameInitFailure','ComdLineHasInvalidChar','InvalidLink','InvalidUrl',
 'ServerOpen','DefaultMapNotFound','GlobalShaderCacheFileMissing','MapNotFoundNoFallback',
 'MapNotFound','ClientOutdated','UE4RequiresProjectFiles','ConnectionFailed'}
core_keys={
 'Cancel','Continue','No','NoToAll','None','OK','Question','Retry','Yes','YesToAll',
 'UrlFailed','GenericLoading','SavingFile','SavingFiles',
 'PureVirtualFunctionCalledWhileRunningApp','IniFileOutOfDate'}
dialog_exclude={'DefaultDebugMessageTitle','UpdateMacOSX_Body','UpdateMacOSX_Title'}
optional_input={'InputKeys','FInputChord','InputKeySelector','SlateAccessibility','EditableTextContextMenu','UICommands.GenericCommands'}
deferred={'CrashReportClient','PreLoadManager.BuildPatchServices','UnrealEngine'}

groups=defaultdict(list)
for i,r in enumerate(rows):
 n,k=r['namespace'],r['key']
 if n in native_full or n=='Engine' and k in engine_keys or n=='Core' and k in core_keys or n=='MessageDialog' and k not in dialog_exclude:
  tier='A_native_system_candidates'
 elif n in optional_input:
  tier='B_optional_input_and_common_text'
 elif n in deferred:
  tier='C_deferred_diagnostic_or_external_surfaces'
 else:
  continue
 groups[tier].append({'engine_index':i,'namespace':n,'key':k,'source_hash':r['source_hash'],'en':r['text']})
for name,selected in groups.items():
 (out/(name+'.json')).write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

summary={
 'source':source.relative_to(root).as_posix(),
 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'locres_version':raw[16],
 'records':len(rows),'namespaces':len(counts),
 'candidate_groups':{name:{'total':len(selected),'namespace_counts':dict(sorted(Counter(r['namespace'] for r in selected).items()))} for name,selected in groups.items()},
 'remaining_unselected':len(rows)-sum(map(len,groups.values())),
 'reachability':'NOT PROVEN; static inventory only; game not launched',
 'engine_translations_written':len(json.loads((root/'translation/arabic/EngineRuntime.json').read_text(encoding='utf-8'))) if (root/'translation/arabic/EngineRuntime.json').exists() else 0,
 'online_plugin_translation_counts':{},
}
for target in ('OnlineSubsystem','OnlineSubsystemSteam','OnlineSubsystemUtils'):
 original=json.loads((root/f'translation/source/{target}.json').read_text(encoding='utf-8'))
 translated=json.loads((root/f'translation/arabic/{target}.json').read_text(encoding='utf-8'))
 assert set(translated)=={str(r['index']) for r in original}
 for r in original:
  en,ar=r['en'],translated[str(r['index'])]
  assert ar and isinstance(ar,str)
  for marker in ('|','^','\r','\n'):
   assert en.count(marker)==ar.count(marker),(target,r['index'],marker)
  for pattern in (r'<[^>]*>',r'\{[^{}]*\}'):
   assert Counter(re.findall(pattern,en))==Counter(re.findall(pattern,ar))
  assert not re.search('[\u202a-\u202e\u2066-\u2069\ufb50-\ufdff\ufe70-\ufeff]',ar)
 summary['online_plugin_translation_counts'][target]=len(translated)
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
