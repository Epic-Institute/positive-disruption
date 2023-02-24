class Chart {
  constructor(data, svg, width, height, margin, scale, popupDiv, tooltipDiv, timeSliderDiv, yAxisTitle, type='line') {
    const vis = this;

    vis.data = data;
    vis.svg = svg;
    vis.width = width;
    vis.height = height;
    vis.margin = margin;
    vis.scale = scale;
    vis.tooltip = new Tooltip(tooltipDiv);
    vis.popup = new Popup(popupDiv);
    vis.yAxisTitle = yAxisTitle;
    vis.type = type;
    vis.formatValue = d3.format(".2s");
    vis.nodata = false;

    vis.colors = ["#00e3e6", "#6797fd", "#6bd384", "#954e9f",
                  "#a84857", "#cce982", "#eba562"]

    vis.transition = 500;

    vis.year = vis.type === 'treemap' ? new Date().getFullYear() : [2010, 2050];
    const fill = vis.type === 'treemap' ? null : '#088184';

    const xmin = d3.min(vis.data.lines, l => d3.min(l.values, d => d.x));
    const xmax = d3.max(vis.data.lines, l => d3.max(l.values, d => d.x));

    const timesliderDim = timeSliderDiv.node().getBoundingClientRect();
    timeSliderDiv.selectAll('svg').remove();

    vis.timeslider = timeSliderDiv.append('svg')
      .attr('width', timesliderDim.width)
      .attr('height', 60)
      .append('g')
      .attr("transform", 'translate(20,10)');

    vis.slider = d3.sliderHorizontal()
      .min(xmin.getFullYear())
      .max(xmax.getFullYear())
      .step(1)
      .width(timesliderDim.width - 60)
      .ticks(5)
      .tickFormat(d => String(d))
      .default(vis.year)
      .fill(fill)
      .handle("M -8, 0 m 0, 0 a 8,8 0 1,0 16,0 a 8,8 0 1,0 -16,0")
      .on('onchange', val => {
        vis.year = val;
        vis.filterData();
        vis.updatePlot();
      })

    vis.timeslider.call(vis.slider);
    vis.timeslider.selectAll(".axis .tick text")
      .attr("y", 12);
    vis.timeslider.selectAll(".parameter-value text")
      .attr("y", 18);
    vis.timeslider.selectAll(".track")
      .remove();

    vis.xScale = d3.scaleTime()
        .range([vis.margin.left, vis.width - vis.margin.right]);
    vis.yScale = d3.scaleLinear()
        .range([vis.height - vis.margin.bottom, 0]);
    if (vis.type === 'line') {
      vis.line = d3.line()
          .curve(d3.curveMonotoneX);
    } else if (vis.type === 'area') {
      vis.area = d3.area();
    } else if (vis.type === 'treemap') {
      vis.treemap = d3.treemap()
        .size([vis.width, vis.height])
        .round(true)
        .padding(1);
    }

    if (vis.type !== 'treemap') {
      vis.xAxis = d3.axisBottom()
        .tickFormat(d => {
          if (d.getFullYear() % 10 === 0) {
            return d3.timeFormat("%Y")(d);
          } else {
            return '';
          }
        })
        .ticks(d3.timeYear.every(1))
        .tickSize(6);
      vis.yAxis = d3.axisLeft()
        .scale(vis.yScale)
        // .tickSize(6);
        // .tickFormat(d => d * 100 + '%')
    }

    vis.g = vis.svg.append("g")
      .attr("transform", "translate(" + vis.margin.left + "," + vis.margin.top + ")");

    vis.filterData();
    vis.initPlot();
  }

  filterData() {
    const vis = this;

    if (vis.type === 'treemap') {
      const obj = {}
      obj['name'] = 'all';
      obj['children'] = vis.data.lines.map(d => {
        let obj2 = {};
        obj2['name'] = d.name;
        obj2['value'] = d.values.filter(val => val.x - d3.timeParse("%Y")(vis.year) === 0)[0].y;
        return obj2;
      })
      vis.filteredData = d3.hierarchy(obj)
        .sum(function(d) { return d.value })
        .sort(function(a, b){ return b.height - a.height || b.value - a.value });

    } else {
      const [minYear, maxYear] = vis.year.map(d => d3.timeParse("%Y")(d));
      vis.filteredData = {}
      vis.filteredData.lines = vis.data.lines.map(line => {
        const obj = {};
        obj.name = line.name;
        obj.values = line.values.filter(value => ((minYear <= value.x) & (value.x <= maxYear)));
        return obj;
      });
    };
  }

  updateData(newData) {
    const vis = this;

    vis.data = newData;
    vis.filteredData = vis.data;
  }

  initPlot() {

    const vis = this;

    vis.gXAxis = vis.svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(" + vis.margin.left + "," + (vis.margin.top + vis.height - vis.margin.bottom) + ")");
    vis.gYAxis = vis.svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(" + (2 * vis.margin.left) + "," + vis.margin.top + ")");

    vis.yLabel = vis.gYAxis.append("g")
        .append("text")
        .attr("class", "y axis-title");

    vis.rule = vis.g.append("g")
      .attr("class", "rule")
      .style("opacity", 0);

    vis.rule.append("line")
      .attr("y1", 0)
      .attr("y2", vis.height - vis.margin.bottom)
      .attr("stroke", "lightgray");
  }

  updatePlot() {
    const vis = this;

    vis.filterData();

    vis.nodata = vis.data.lines.length === 0;

    if (vis.nodata === true) {
      vis.svg.style("opacity", 0);
      let offset = vis.svg.node().getBoundingClientRect();
      vis.popup.update('<div class="legend"><div class="legend-header">No data matches current selection</div></div>',
                        offset.left + vis.margin.left + vis.width / 2,
                        vis.margin.top + offset.top + vis.height / 2);
    } else if (vis.type === 'treemap') {
      vis.svg.style("opacity", 1);
      vis.popup.hide();
      vis.treemap(vis.filteredData);
      vis.updateRects();
    } else {
      vis.svg.style("opacity", 1);
      vis.popup.hide();
      vis.updateAxes();
      vis.updateCurves();
    }
  }

  updateAxes() {

    const vis = this;

    // x-axis
    // let xmin = d3.min(vis.filteredData.lines, l => d3.min(l.values, d => d.x));
    // let xmax = d3.max(vis.filteredData.lines, l => d3.max(l.values, d => d.x));
    [vis.xmin, vis.xmax] = vis.year.map(d => d3.timeParse("%Y")(d));
    vis.xScale.domain([vis.xmin, vis.xmax]);
    vis.xAxis.scale(vis.xScale);

    let ymin, ymax;
    if (vis.type === 'line') {
      ymin = d3.min(vis.filteredData.lines, l => d3.min(l.values, d => d.y));
      ymax = d3.max(vis.filteredData.lines, l => d3.max(l.values, d => d.y));
    } else if (vis.type === 'area') {
      ymin = d3.min(vis.filteredData.lines, l => d3.min(l.values, d => d.y0));
      ymax = d3.max(vis.filteredData.lines, l => d3.max(l.values, d => d.y1));
    }

    vis.yScale.domain([ymin, ymax]);
    vis.yAxis.scale(vis.yScale)

    let nTicks = 5;
    let yValues = vis.yAxis.scale().ticks();
    let deltaY = (yValues[1] - yValues[0]) / nTicks;
    let yNewValues = ymin < 0 ?
                  [...d3.range(yValues[0] + deltaY, ymin, -deltaY).reverse(), ...d3.range(yValues[0], ymax, deltaY)] :
                  [...d3.range(yValues[0] - deltaY, ymin, -deltaY).reverse(), ...d3.range(yValues[0], ymax, deltaY)];

    vis.yScale.domain([ymin, ymax]);
    vis.yAxis.scale(vis.yScale)
      .tickFormat(d => {
        if (yValues.includes(d)) {
          return vis.formatValue(d);
        } else {
          return '';
        }
      })
      .tickValues(yNewValues);

    if (vis.type === 'line') {
      vis.line.x((d, i) => vis.xScale(d.x))
        .y((d, i) => vis.yScale(d.y));
    } else if (vis.type === 'area') {
      vis.area.x(d => vis.xScale(d.x))
        .y0(d => vis.yScale(d.y0))
        .y1(d => vis.yScale(d.y1));
    }

    // if (vis.scale === "log"){
    //   let yMax = d3.max(vis.data.lines, l => d3.max(l.values, d => d.y)) + 1;
    //   vis.yScale = d3.scaleLog()
    //       .range([vis.height - vis.margin.bottom, 0])
    //       .domain([1, yMax])
    //   let tickValues = d3.range(yMax.toString().length)
    //     .map(d => [1 * 10**d, 2 * 10**d, 5 * 10**d])
    //     .flat()
    //     .filter(d => d <= yMax);
    //   vis.yAxis = d3.axisLeft()
    //       .scale(vis.yScale)
    //       .tickValues(tickValues)
    //       .tickFormat(d3.format('i'))
    //   vis.line.x((d, i) => vis.xScale(d.x))
    //     .y(d => vis.yScale(d.y + 1));
    // } else if (this.scale === "linear") {
    //   let yMax = 1.0;
    //   vis.yScale = d3.scaleLinear()
    //       .range([vis.height - vis.margin.bottom, 0])
    //       .domain([0, yMax]).nice()
    //   vis.yAxis = d3.axisLeft()
    //       .scale(vis.yScale)
    //       .tickFormat(d => {
    //         if (Math.round(d * 100) % 10 === 0) {
    //           return Math.round(d * 100) + '%';
    //         } else {
    //           return '';
    //         }
    //       })
    //       .tickValues(d3.range(0, 1.01, 0.01))
    //       .tickSize(6)
    //   vis.line.x((d, i) => vis.xScale(d.x))
    //     .y((d, i) => vis.yScale(d.y));
    // }

    vis.gXAxis.call(vis.xAxis);
    vis.gYAxis.call(vis.yAxis);

    vis.gXAxis.selectAll(".domain").remove();
    vis.gYAxis.selectAll(".domain").remove();

    vis.gXAxis.selectAll(".tick").attr("class", d => {
      if (d.getFullYear() % 10 === 0) {
        return 'tick big-tick';
      } else {
        return 'tick small-tick';
      }
    });

    vis.gYAxis.selectAll(".tick").attr("class", d => {
      if (yValues.includes(d)) {
        return 'tick big-tick';
      } else {
        return 'tick small-tick';
      }
    });

    vis.gXAxis.selectAll(".small-tick").select("line")
      .attr("y2", 4)
    vis.gYAxis.selectAll(".small-tick").select("line")
      .attr("x2", -4);

    vis.yLabel
      .attr("text-anchor", "start")
      .style("font-size", "12px")
      .attr("fill", "white")
      .attr("transform", "translate(-20, -5)")
      .text(vis.yAxisTitle);

  }; // updateAxes

  updateCurves() {
    const vis = this;

    const historicalDate = 2020;
    const histDate = d3.timeParse("%Y")(historicalDate);

    const firstDate = d3.max([vis.xScale.domain()[0], histDate]);
    const lastDate = d3.min([vis.xScale.domain()[1], vis.xmax]);
    const dataProjection = lastDate - firstDate > 0;

    if (dataProjection) {
      vis.rect = vis.g.selectAll("rect").data([[firstDate, lastDate]]);
    
      vis.rect.enter().append('rect')
        .transition()
        .duration(vis.transition)
        .attr('x', d => vis.xScale(d[0]))
        .attr('y', 0)
        .attr('width', d => vis.xScale(d[1]) - vis.xScale(d[0]))
        .attr('height', vis.height - vis.margin.bottom)
        .attr("fill", '#165163')
        .attr("opacity", 0.2);
  
      vis.rect
        .transition()
        .duration(vis.transition)
        .attr('x', d => vis.xScale(d[0]))
        .attr('y', 0)
        .attr('width', d => vis.xScale(d[1]) - vis.xScale(d[0]))
        .attr('height', vis.height - vis.margin.bottom)
        .attr("fill", '#165163')
        .attr("opacity", 0.2);
  
      vis.rect.exit().remove();
  
      vis.label = vis.g.selectAll(".projection-label").data([[firstDate, lastDate]]);
      
      vis.label.enter().append('text')
        .transition()
        .duration(vis.transition)
        .attr("class", "projection-label")
        .attr('x', d => vis.xScale(d[0]) + 14)
        .attr('y', 20)      
        .attr("fill", 'lightgray')
        .text("Projection");
  
      vis.label
        .transition()
        .duration(vis.transition)
        .attr("class", "projection-label")
        .attr('x', d => vis.xScale(d[0]) + 14)
        .attr('y', 20)      
        .attr("fill", 'lightgray')
        .text("Projection");
  
      vis.label.exit().remove();
    } else {
      vis.rect.remove();
      vis.label.remove();
    }
    

    vis.path = vis.g.selectAll("path").data(vis.filteredData.lines);

    vis.path.enter().append("path")
      .transition()
      .duration(vis.transition)
      .attr("fill", vis.type === 'area' ? curveColor : "none")
      .attr("stroke-width", curveWidth)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      // .style("mix-blend-mode", "multiply")
      .attr("opacity", curveOpacity)
      // .attr("class", d => "curve "+nameNoSpaces(d.Sector))
      .attr("stroke", vis.type === 'line' ? curveColor : "none")
      .attr("d", d => vis.type === 'line' ? vis.line(d.values) : vis.type === 'area' ? vis.area(d.values) : null);

    vis.path.transition()
      .duration(vis.transition)
      .attr("fill", vis.type === 'area' ? curveColor : "none")
      .attr("stroke-width", curveWidth)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      // .style("mix-blend-mode", "multiply")
      .attr("opacity", curveOpacity)
      // .attr("class", d => "curve "+nameNoSpaces(d.Sector))
      .attr("stroke", vis.type === 'line' ? curveColor : "none")
      .attr("d", d => vis.type === 'line' ? vis.line(d.values) : vis.type === 'area' ? vis.area(d.values) : null);

    vis.path.exit().remove();

    if (dataProjection) {
      const guideDate = histDate - firstDate === 0 ? firstDate : [];
      vis.guideline = vis.g.selectAll(".projection-line").data([guideDate]);
    
      vis.guideline.enter().append('line')
        .transition()
        .duration(vis.transition)
        .attr("class", "projection-line")
        .attr('x1', d => vis.xScale(d))
        .attr('y1', 0)
        .attr('x2', d => vis.xScale(d))
        .attr('y2', vis.height - vis.margin.bottom)     
        .attr("stroke", 'lightgray')
        .attr("stroke-dasharray", "4,4")
        .attr("stroke-width", 0.5);

      vis.guideline
        .transition()
        .duration(vis.transition)
        .attr("class", "projection-line")
        .attr('x1', d => vis.xScale(d))
        .attr('y1', 0)
        .attr('x2', d => vis.xScale(d))
        .attr('y2', vis.height - vis.margin.bottom)     
        .attr("stroke", 'lightgray')
        .attr("stroke-dasharray", "4,4")
        .attr("stroke-width", 0.5);

      vis.guideline.exit().remove();
    } else {
      vis.guideline.remove();
    }
    
    vis.rule.raise();
    if (vis.type !== 'treemap') vis.svg.call(hover, vis.path);

    function curveOpacity(d) {
      return vis.type === 'area' ? 0.8 : 1.0;
    }

    function curveColor(d, i) {
      return vis.colors[i % vis.colors.length]
    }

    function curveWidth(d) {
      return 1.5;
    }

    function circleRadius(d) {
      const radius = 3.0;
      return vis.type === 'line' ? radius : d.y === d.y1 ? 0 : radius;
    }

    function getCircleHtml(color) {
      let circleRadius = 4;
      return `<svg width="${2 * circleRadius}px" height="${2 * circleRadius}px"><circle cx="${circleRadius}px" cy="${circleRadius}px" r="${circleRadius}px" fill="${color}"></circle></svg>`
    }

    function hover(svg, path) {
      if ("ontouchstart" in document) svg
          .style("-webkit-tap-highlight-color", "transparent")
          .on("touchmove", moved)
          // .on("touchstart", entered)
          .on("touchend", left)
          // .on("touch", click);
      else svg
          .on("mousemove", moved)
          // .on("mouseenter", entered)
          .on("mouseleave", left)
          // .on("click", click);

      function left() {
        d3.selectAll(".rule")
          .style("opacity", 0);
        vis.tooltip.hide();
      }

      function moved(event) {
        if (vis.nodata === false) {
          let thisX = d3.pointer(event, this)[0] - vis.margin.left;
          if ((vis.margin.left < thisX) && (thisX < vis.width - vis.margin.right)) {
            const xm = vis.xScale.invert(thisX),
              xYear = xm.getFullYear(),
              xPoint = new Date(xYear, 1, 1);
            let dataValues = vis.data.lines.map((d, i) => {
              let obj = {};
              obj.name = d.name;
              let filteredValue = d.values.filter(v => v.x.getFullYear() === xYear)[0];
              if (vis.type === 'line') {
                obj.y = filteredValue.y;
              } else if (vis.type === 'area') {
                obj.y = filteredValue.y1 - filteredValue.y0;
                obj.y1 = filteredValue.y1;
              }
              obj.color = curveColor(d, i);
              return obj;
            });

            let legendHtml = dataValues.sort((a,b) => vis.type === 'area' ? b.y1 - a.y1 : b.y - a.y)
              .map((d,i) => {
                let spanCircle = `<span class="legend-circle">${getCircleHtml(d.color)}</span>`,
                    spanName = `<span class="legend-name">${d.name}</span>`,
                    spanNumber = `<span class="legend-value">${vis.formatValue(d.y)}</span>`;

                return `<div class="legend-item">${spanCircle}${spanName}${spanNumber}</div>`;
              })
              .reduce((a,b) => a + b, "");

            d3.selectAll(".rule")
              .attr("transform", `translate(${vis.xScale(xPoint)},0)`)
              .style("opacity", 1);

            if (vis.type === 'line') {
              let dots = vis.rule.selectAll(".circle-plot")
                .data(dataValues);

              dots.enter().append("circle")
                .attr("class", "circle-plot")
                .attr("cx", 0)
                .attr("cy", d => vis.type === 'line' ? vis.yScale(d.y) : vis.yScale(d.y1))
                .attr("r", circleRadius)
                .attr("fill", d => d.color)

              dots.attr("class", "circle-plot")
                .attr("cx", 0)
                .attr("cy", d => vis.type === 'line' ? vis.yScale(d.y) : vis.yScale(d.y1))
                .attr("r", circleRadius)
                .attr("fill", d => d.color)

              dots.exit().remove();
            }

            let offset = vis.svg.node().getBoundingClientRect();
            vis.tooltip.update(`<div class="legend"><div class="legend-header">${xYear}</div><div class="legend-body">${legendHtml}</div></div>`,
                                offset.left + vis.margin.left + vis.xScale(xPoint),
                                document.documentElement.scrollTop + vis.margin.top + offset.top,
                                'right');
          } else {
            d3.selectAll(".rule")
              .style("opacity", 0);
            vis.tooltip.hide();
          }
        }
      }  
    }
  } // updateCurves

  updateRects() {
    const vis = this;

    function notHover(svg, path) {
      const doNothing = () => null;

      if ("ontouchstart" in document) svg
          .style("-webkit-tap-highlight-color", "transparent")
          .on("touchmove", doNothing)
          // .on("touchstart", entered)
          .on("touchend", () => vis.tooltip.hide())
          // .on("touch", click);
      else svg
          .on("mousemove", doNothing)
          // .on("mouseenter", entered)
          .on("mouseleave", () => vis.tooltip.hide())
          // .on("click", click);
    }

    vis.svg.call(notHover, vis.path);

    function rectColor(d, i) {
      return vis.colors[i % vis.colors.length]
    }

    function handleMouseOver(event, d) {
      let thisX = d3.pointer(event, this)[0],
          thisY = d3.pointer(event, this)[1];
      let offset = vis.svg.node().getBoundingClientRect();
      vis.tooltip.update(`<div class="legend"><div class="legend-header">${d.data.name}</div><div class="legend-body">${vis.formatValue(d.value)}</div></div>`,
                          offset.left + thisX,
                          document.documentElement.scrollTop + offset.top + thisY,
                          'top');
    }

    var cell = vis.g.selectAll("rect")
      .data(vis.filteredData.leaves());

    cell.enter().append("rect")
      .attr("id", function(d) { return d.id; })
      .attr("width", function(d) { return d.x1 - d.x0; })
      .attr("height", function(d) { return d.y1 - d.y0; })
      .attr("x", d => d.x0)
      .attr("y", d => d.y0)
      .attr("fill", rectColor)
      .on("mousemove", handleMouseOver);

    cell
      .attr("id", function(d) { return d.id; })
      .attr("width", function(d) { return d.x1 - d.x0; })
      .attr("height", function(d) { return d.y1 - d.y0; })
      .attr("x", d => d.x0)
      .attr("y", d => d.y0)
      .attr("fill", rectColor)
      .on("mousemove", handleMouseOver);

    cell.exit().remove();

    cell.append("clipPath")
        .attr("id", function(d) { return "clip-" + d.id; })
      .append("use")
        .attr("xlink:href", function(d) { return "#" + d.id; });

    var label = vis.g.selectAll(".rect-label")
      .data(vis.filteredData.leaves().filter(d => ((d.x1 - d.x0) * (d.y1 - d.y0) > 50) & (d.x1 - d.x0 > 50) & (d.y1 - d.y0 > 50)));

    label.enter().append("text")
      .attr("class", "rect-label");

    label
      .attr("class", "rect-label");

    label.exit().remove();

    var rectLabels = vis.g.selectAll(".rect-label").selectAll("tspan")
      .data(d => [[d.data.name, d.x0, d.y0, 'name'], [d.value, d.x0, d.y0, 'value']])

    rectLabels.enter().append("tspan")
      .attr("x", d => d[1])
      .attr("y", (d, i) => d[2] + 14 * (i + 1))
      .text(d => d[3] === 'name' ? d[0] : vis.formatValue(d[0]));

    rectLabels
      .attr("x", d => d[1])
      .attr("y", (d, i) => d[2] + 14 * (i + 1))
      .text(d => d[3] === 'name' ? d[0] : vis.formatValue(d[0]));

    rectLabels.exit().remove();

  } // updateRects

  hideRule () {
    d3.selectAll(".rule")
      .style("opacity", 0);
  }
}
