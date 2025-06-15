import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CodeDocsComponent } from './code-docs.component';

describe('CodeDocsComponent', () => {
  let component: CodeDocsComponent;
  let fixture: ComponentFixture<CodeDocsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CodeDocsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CodeDocsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
