import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GithubDocComponent } from './github-doc.component';

describe('GithubDocComponent', () => {
  let component: GithubDocComponent;
  let fixture: ComponentFixture<GithubDocComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GithubDocComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GithubDocComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
