import { Component, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import * as d3 from 'd3';

@Component({
  selector: 'app-db-docs',
  standalone: true,
  template: `<div #chartContainer></div>`,
  styles: [`
    :host { display: block; height: 100%; }
    div { width: 100%; height: 600px; border: 1px solid #eee; }
  `]
})
export class DbDocsComponent implements AfterViewInit {
  @ViewChild('chartContainer', { static: true }) 
  private chartContainer!: ElementRef<HTMLDivElement>;

  ngAfterViewInit(): void {
    this.renderDatabaseSchema();
  }

  private renderDatabaseSchema(): void {
    const data = {
      tables: [
        { 
          name: 'Devices', 
          fields: ['id: PK', 'name: VARCHAR', 'status: BOOL'],
          x: 100, 
          y: 100 
        },
        { 
          name: 'Users', 
          fields: ['id: PK', 'login: VARCHAR', 'role: INT'],
          x: 400, 
          y: 100 
        }
      ],
      relations: [
        { source: 'Devices', target: 'Users', type: 'many-to-one' }
      ]
    };

    const container = this.chartContainer.nativeElement;
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%');

    // Отрисовка таблиц
    const tables = svg.selectAll('.table')
      .data(data.tables)
      .enter()
      .append('g')
      .attr('class', 'table')
      .attr('transform', (d: any) => `translate(${d.x},${d.y})`);

    tables.append('rect')
      .attr('width', 200)
      .attr('height', (d: any) => 100 + d.fields.length * 25)
      .attr('fill', '#f8f9fa')
      .attr('stroke', '#495057');

    // Отрисовка связей
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5');

    data.relations.forEach((rel: any) => {
      const source = data.tables.find(t => t.name === rel.source);
      const target = data.tables.find(t => t.name === rel.target);
      
      if (source && target) {
        svg.append('path')
          .attr('marker-end', 'url(#arrowhead)')
          .attr('d', `M${source.x + 100},${source.y + 50} L${target.x},${target.y + 50}`)
          .attr('stroke', '#666')
          .attr('fill', 'none');
      }
    });
  }
}