import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DbDocsComponent } from './db-docs.component';

describe('DbDocsComponent', () => {
  let component: DbDocsComponent;
  let fixture: ComponentFixture<DbDocsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DbDocsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DbDocsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
