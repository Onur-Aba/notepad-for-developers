from __future__ import annotations

from PySide6.QtWidgets import QCheckBox,QComboBox,QDialog,QDialogButtonBox,QFileDialog,QFormLayout,QLabel,QMessageBox,QVBoxLayout

from app.i18n import I18n
from app.services.workspace_transfer import ExportOptions,ProjectTransferService

class _OptionsMixin:
    def _build_options(self,root:QVBoxLayout,available:dict[str,bool]|None=None)->None:
        tr=self.i18n.language=="tr"; self.checks={}; labels={"notes":("Notlar","Notes"),"decisions":("Kararlar","Decisions"),"architecture":("Mimari","Architecture"),"repositories":("Repository metadata","Repository metadata"),"links":("Kod bağlantıları","Code links"),"review_history":("Review/geçmiş","Review/history"),"tags":("Etiketler","Tags"),"activity":("Aktivite zaman çizelgesi","Activity timeline")}
        for key in ExportOptions.__dataclass_fields__:
            c=QCheckBox(labels[key][0 if tr else 1]); c.setChecked(True if available is None else bool(available.get(key,False))); c.setEnabled(True if available is None else bool(available.get(key,False))); self.checks[key]=c; root.addWidget(c)
    def options(self)->ExportOptions:return ExportOptions(**{k:c.isChecked() for k,c in self.checks.items()})

class ExportProjectDialog(QDialog,_OptionsMixin):
    def __init__(self,service:ProjectTransferService,project_id:int,i18n:I18n,parent=None)->None:
        super().__init__(parent); self.service=service; self.project_id=project_id; self.i18n=i18n; tr=i18n.language=="tr"; self.output_path=None
        self.setWindowTitle("Projeyi Dışa Aktar" if tr else "Export Project"); root=QVBoxLayout(self); intro=QLabel("Nelerin dışa aktarılacağını seçin." if tr else "Choose what to export."); intro.setObjectName("helperBanner"); root.addWidget(intro); self._build_options(root)
        self.format=QComboBox(); self.format.addItem("ZIP (.zip)",True); self.format.addItem("Markdown klasörü" if tr else "Markdown folder",False); root.addWidget(self.format)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save); buttons.button(QDialogButtonBox.StandardButton.Save).setText("Dışa aktar" if tr else "Export"); buttons.accepted.connect(self._export); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def _export(self)->None:
        tr=self.i18n.language=="tr"; as_zip=bool(self.format.currentData())
        if as_zip:path,_=QFileDialog.getSaveFileName(self,"ZIP","devnest-project.zip","ZIP (*.zip)")
        else:path=QFileDialog.getExistingDirectory(self,"Klasör seç" if tr else "Choose folder")
        if not path:return
        try:self.output_path=self.service.export_project(self.project_id,path,self.options(),as_zip=as_zip)
        except Exception as exc:QMessageBox.critical(self,"Export",str(exc));return
        self.accept()

class ImportProjectDialog(QDialog,_OptionsMixin):
    def __init__(self,service:ProjectTransferService,source,i18n:I18n,parent=None)->None:
        super().__init__(parent); self.service=service; self.source=source; self.i18n=i18n; self.project_id=None; tr=i18n.language=="tr"; manifest=service.read_manifest(source)
        self.setWindowTitle("Projeyi İçe Aktar" if tr else "Import Project"); root=QVBoxLayout(self); project=manifest.get("project") or {}; counts={"notes":len(manifest.get("notes",[])),"decisions":len(manifest.get("decisions",[])),"architecture":len(manifest.get("architecture",[])),"repositories":len(manifest.get("repositories",[])),"links":len(manifest.get("resource_links",[])),"review_history":len(manifest.get("review_history",[])),"tags":1 if any(x.get("tags") for x in list(manifest.get("notes",[]))+list(manifest.get("decisions",[]))) else 0,"activity":len(manifest.get("activity",[]))}
        intro=QLabel((f"Kurulacak proje: {project.get('name')}\nİçerik: "+", ".join(f"{k}={v}" for k,v in counts.items())) if tr else (f"Project to import: {project.get('name')}\nContents: "+", ".join(f"{k}={v}" for k,v in counts.items()))); intro.setWordWrap(True); intro.setObjectName("helperBanner"); root.addWidget(intro); self._build_options(root,{k:v>0 for k,v in counts.items()})
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok); buttons.button(QDialogButtonBox.StandardButton.Ok).setText("İçe aktar" if tr else "Import"); buttons.accepted.connect(self._import); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def _import(self)->None:
        try:self.project_id=self.service.import_project(self.source,self.options())
        except Exception as exc:QMessageBox.critical(self,"Import",str(exc));return
        self.accept()
