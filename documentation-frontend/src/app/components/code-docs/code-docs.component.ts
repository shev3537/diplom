import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIf, NgForOf } from '@angular/common';

interface CodeDocFile {
  name: string;
  module_docstring?: string;
  classes: { name: string; docstring?: string }[];
  functions: { name: string; docstring?: string }[];
}

@Component({
  selector: 'app-code-docs',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIf, NgForOf],
  templateUrl: './code-docs.component.html',
  styleUrls: ['./code-docs.component.css']
})
export class CodeDocsComponent {
  @Input() docs: { files: CodeDocFile[] } | null = null;
  searchText = '';

  filteredFiles(): CodeDocFile[] {
    if (!this.docs?.files) return [];
    if (!this.searchText) return this.docs.files;
    const q = this.searchText.toLowerCase();
    return this.docs.files.filter(file =>
      file.name.toLowerCase().includes(q) ||
      (file.classes && file.classes.some(cls => cls.name.toLowerCase().includes(q))) ||
      (file.functions && file.functions.some(fn => fn.name.toLowerCase().includes(q)))
    );
  }
}
