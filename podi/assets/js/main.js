let state = {
  region: regions[0],
  region_info: null,
  scenario: 'baseline',
  vector: vectors[0],
  result: vectors[0],
  filteredData: null,
  rawData: null,
  chart: 'line',
  groupBy: null,
  rawUniqueItems: {},
  filteredUniqueItems: {}
}

d3.select("#about-button")
  .on("click", function(d){
    document.getElementById("about-details").classList.toggle("show");
  });

d3.select("#close")
  .on("click", function(d){
    document.getElementById("about-details").classList.toggle("show");
  });

const CIAFields = {
  'Economy': ["Real GDP per capita", "Real GDP growth rate", "Inflation rate (consumer prices)", "Unemployment rate"],
  'Energy': ["Electricity access", "Carbon dioxide emissions", "Energy consumption per capita"],
  'Environment': ["Revenue from forest resources", "Revenue from coal"]
};

const graphTypes = ['line', 'area', 'treemap'];

let graphs = d3.select('#chart-types').selectAll("div")
  .data(graphTypes);

graphs.enter().append("div")
  .attr("class", "chart-icon col-2")
  .html(d => `<img src="img/chart-icons/${d}.svg" /><span class="icon-name">${d.split("_").join(' ')}</span>`)
  .on("click", (event, d) => {
    if (state.chart !== d) {
      state.chart = d;
      d3.select("#chart svg").selectAll("g").remove();
      loadData('./data/'+state.result.folder+'/'+state.region.name+'.csv');
    }
  });

graphs.html(d => `<img src="img/chart-icons/${d}.svg" /><span class="icon-name">${d.split("_").join(' ')}</span>`)
  .attr("class", "chart-icon col-2")
  .on("click", (event, d) => {
    if (state.chart !== d) {
      state.chart = d;
      d3.select("#chart svg").selectAll("g").remove();
      loadData('./data/'+state.result.folder+'/'+state.region.name+'.csv');
    }
  });

graphs.exit().remove();


function getCIA(url) {
  Promise.all([d3.json(url)]).then(function(data){
    state.region_info = data[0];
    updateRegionInfo();
  })
}

getCIA(state.region.url)

function getHtml(indicator) {

  const text = indicator[Object.keys(indicator)[0]].text;
  const i = text.indexOf(' ');

  const number = Object.keys(indicator)[0] === 'total emissions' ? d3.format(".3s")(+text.slice(0, i).replace(/,/g, '')): text.slice(0, i);
  const est = text.slice(i + 1);

  return `<span class="cia-number">${number}</span><span class="cia-est">${est}</span>`

}

function updateIndicator(id, field) {
  let economy = state.region_info["Economy"];

  d3.select(id).html(getHtml(economy[field]));
  let width = d3.select(id).select(".cia-number").node().getBoundingClientRect().width;
  d3.select(id).select(".cia-est")
    .style("left", width + 'px');
}

function updateRegionInfo() {
  d3.select("#region-name").html(state.region.short_name);

  let ciaDivs = d3.select(".cia-indicators").selectAll(".cia-indicator")
    .data(Object.keys(CIAFields));

  ciaDivs.enter().append("div")
    .attr("class", "cia-indicator");

  ciaDivs.attr("class", "cia-indicator");

  ciaDivs.exit().remove();

  let indicatorName = d3.select(".cia-indicators").selectAll(".cia-indicator").selectAll(".indicator-name")
    .data(d => [d]);

  indicatorName.enter().append("div")
    .attr("class", "indicator-name")
    .html(d => d)
    .on("click", (event, d) => {
      let target = d3.select(event.target);
      let sibling = d3.select(event.target.parentNode).select(".indicator-details");
      let thisChecked = target.classed("checked");

      if (thisChecked === true) {
        target.classed("checked", false);
        sibling.classed("show", false);
      } else {
        d3.selectAll(".indicator-name")
          .classed("checked", c => c === d);
        d3.selectAll(".indicator-details")
          .classed("show", c => c === d); 

        d3.select(".cia-indicators")
          .selectAll(".cia-indicator")
          .selectAll(".indicator-details")
          .selectAll(".indicator-col")
          .selectAll(".indicator-value")
          .each((d,i,node) => {
            let thisNode = d3.select(node[0]);
            if (thisNode.select(".cia-number").node() !== null) {
              let width = thisNode.select(".cia-number").node().getBoundingClientRect().width;
              thisNode.select(".cia-est")
                .style("left", width + "px");
            }
          });
      }
    });

  indicatorName.attr("class", "indicator-name")
    .html(d => d)
    .on("click", (event, d) => {
      let target = d3.select(event.target);
      let sibling = d3.select(event.target.parentNode).select(".indicator-details");
      let thisChecked = target.classed("checked");

      if (thisChecked === true) {
        target.classed("checked", false);
        sibling.classed("show", false);
      } else {
        d3.selectAll(".indicator-name")
          .classed("checked", c => c === d);
        d3.selectAll(".indicator-details")
          .classed("show", c => c === d); 

        d3.select(".cia-indicators")
          .selectAll(".cia-indicator")
          .selectAll(".indicator-details")
          .selectAll(".indicator-col")
          .selectAll(".indicator-value")
          .each((d,i,node) => {
            let thisNode = d3.select(node[0]);
            let width = thisNode.select(".cia-number").node().getBoundingClientRect().width;
            thisNode.select(".cia-est")
              .style("left", width + "px")
          });
      }
    });

  indicatorName.exit().remove();


  let indicatorDetails = d3.select(".cia-indicators").selectAll(".cia-indicator").selectAll(".indicator-details")
    .data(d => [d]);

  indicatorDetails.enter().append("div")
    .attr("class", "indicator-details row");

  indicatorDetails.attr("class", "indicator-details row");

  indicatorDetails.exit().remove();

  let indicatorCol = d3.select(".cia-indicators").selectAll(".cia-indicator").selectAll(".indicator-details").selectAll(".indicator-col")
    .data(d => CIAFields[d].map(f => [d, f]));

  indicatorCol.enter().append("div")
    .attr("class", 'indicator-col col-6');

  indicatorCol
    .attr("class", 'indicator-col col-6');

  indicatorCol.exit().remove();

  let indicatorValues = d3.select(".cia-indicators").selectAll(".cia-indicator").selectAll(".indicator-details").selectAll(".indicator-col").selectAll(".indicator-value")
    .data(d => [d]);

  indicatorValues.enter().append("div")
    .attr("class", 'indicator-value row')
    .html(d => state.region_info[d[0]][d[1]] ? getHtml(state.region_info[d[0]][d[1]]) : '')
    .each((d,i,node) => {
      let thisNode = d3.select(node[0]);
      if (thisNode.select(".cia-number").node() !== null) {
        let width = thisNode.select(".cia-number").node().getBoundingClientRect().width;
        thisNode.select(".cia-est")
          .style("left", width + "px");
      }
    });

  indicatorValues
    .attr("class", 'indicator-value row')
    .html(d => state.region_info[d[0]][d[1]] ? getHtml(state.region_info[d[0]][d[1]]) : '')
    .each((d,i,node) => {
      let thisNode = d3.select(node[0]);
      if (thisNode.select(".cia-number").node() !== null) {
        let width = thisNode.select(".cia-number").node().getBoundingClientRect().width;
        thisNode.select(".cia-est")
          .style("left", width + "px");
      }
    });

  indicatorValues.exit().remove();

  let indicatorValuesNames = d3.select(".cia-indicators").selectAll(".cia-indicator").selectAll(".indicator-details").selectAll(".indicator-col").selectAll(".indicator-value-name")
    .data(d => [d]);

  indicatorValuesNames.enter().append("div")
    .attr("class", 'indicator-value-name row')
    .html(d => state.region_info[d[0]][d[1]] === undefined ? '' : `<span class="cia-indicator-name">${d[1]}</span>`)

  indicatorValuesNames
    .attr("class", 'indicator-value-name row')
    .html(d => state.region_info[d[0]][d[1]] === undefined ? '' : `<span class="cia-indicator-name">${d[1]}</span>`);

  indicatorValuesNames.exit().remove();
}

function addOptions(id, rawValues) {
  var element = d3.select("#"+id);

  var buttonsDiv = element.selectAll("div").data([["Select all", "Deselect all"]]);

  buttonsDiv.enter().append("div")
    .attr("class", "buttons-container");

  buttonsDiv
    .attr("class", "buttons-container");

  buttonsDiv.exit().remove();

  var buttons = element.selectAll("div").selectAll("span").data(d => d);

  buttons.enter().append("span")
    .html(d => d);

  buttons.html(d => d);

  buttons.exit().remove();

  var options = element.selectAll("a").data(rawValues);

  options.enter().append("a");

  options.exit().remove();

  var optionsCheckboxes = element.selectAll("a").selectAll("input").data(d => [d]);

  // Checkboxes
  optionsCheckboxes.enter().append("input")
    .attr("type", "checkbox")
    .attr("id", d => nameNoSpaces(d.name))
    .property("checked", d => d.selected);

  optionsCheckboxes
    .attr("type", "checkbox")
    .attr("id", d => nameNoSpaces(d.name))
    .property("checked", d => d.selected);

  optionsCheckboxes.exit().remove();

  // Labels
  var optionsLabels = element.selectAll("a").selectAll("label").data(d => [d.name]);

  optionsLabels.enter().append("label")
    .attr("for", d => nameNoSpaces(d))
    .html(d => d);

  optionsLabels.exit().remove();

  return element;
}

function addStandardOptions(id, values, attrs=values.map(d => null)) {
  var element = d3.select("#"+id);
  var options = element.selectAll("option").data(values);

  options.enter().append("option")
    .attr("value", (d,i) => attrs[i])
    .html(d => d);

  options.attr("value", (d,i) => attrs[i])
    .html(d => d);

  options.exit().remove();

  return element;
}

function addButtons(id, values) {
  var element = d3.select("#"+id);
  var options = element.selectAll("button").data(values);

  options.enter().append("button")
    .attr("class", "btn-ei")
    .html(d => d);

  options.exit().remove();

  return element;
}

function updateDropdownLabel(id, label) {
  d3.select(id).select(".dropbtn").html(label);
}

function updateSelectedButton(element, stateVar) {
  element.selectAll(".btn-ei").filter(d => d !== stateVar).classed("btn-ei-selected", false);
  element.selectAll(".btn-ei").filter(d => d === stateVar).classed("btn-ei-selected", true);
}

function hideCountryDivs() {
  d3.select(".select-vector").style("display", "none");
}

function showCountryDivs() {
  d3.select(".select-vector").style("display", "block");
}

let selectRegion = d3.select("#regions-menu");
let searchBox = d3.select("#search-box");
let searchReset = d3.select("#reset-search");

function updateRegions(regionsData) {

  let optionsRegion = selectRegion.selectAll("a").data(regionsData);

  optionsRegion.html(d => d.short_name)
    .on("click", (event, d) => {
      if (d.name !== state.region.name) {
        state.region = d;
        getCIA(d.url);
        updateDropdownLabel("#dropdown-region", state.region.short_name);
        d3.select("#chart svg").selectAll("g").remove();
        loadData('./data/'+state.result.folder+'/'+state.region.name+'.csv');
      }
    });

  optionsRegion.enter().append("a")
    .html(d => d.short_name)
    .on("click", (event, d) => {
      if (d.name !== state.region.name) {
        state.region = d;
        getCIA(d.url);
        updateDropdownLabel("#dropdown-region", state.region.short_name);
        d3.select("#chart svg").selectAll("g").remove();
        loadData('./data/'+state.result.folder+'/'+state.region.name+'.csv');
      }
    });

  optionsRegion.exit().remove();
}

updateRegions(regions);

d3.select("#dropbtn-region")
  .on("click", function(d){
    document.getElementById("regions-menu").classList.toggle("show");
    document.getElementById("regions-search").classList.toggle("show");
    searchBox.attr("placeholder", "Search...");
    chart.hideRule();
    chart.tooltip.hide();
  });
updateDropdownLabel("#dropdown-region", state.region.short_name);

searchBox
  .on("click", (event) => {
    searchBox.attr("placeholder", "");
  })
  .on("keyup",  (event) => {
    let searchLabel = searchBox.property("value");

    if (searchLabel.length > 0) {
      searchReset.classed("show", true);
      let regionsData = regions.filter(d => d.short_name.toLowerCase().includes(searchLabel.toLowerCase()));
      updateRegions(regionsData);
    } else {
      searchReset.classed("show", false);
      updateRegions(regions);
    }
  });

searchReset
  .on("click", () => {
    searchBox.property("value", '')
      .attr("placeholder", "Search...");
    searchReset.classed("show", false);
    updateRegions(regions);
  });

let selectVector = d3.select("#buttons-vector");

let options = selectVector.selectAll("button").data(vectors);

options.enter().append("button")
  .attr("class", "btn-ei")
  .html(d => d.name);

options.exit().remove();

updateSelectedButton(selectVector, state.result);
selectVector.selectAll(".btn-ei").on("click", (event, d) => {
  if (state.result !== d) {
    state.result = d;
    updateSelectedButton(selectVector, state.result);
    chart.hideRule();
    chart.tooltip.hide();
    d3.select("#chart svg").selectAll("g").remove();
    loadData('./data/'+state.result.folder+'/'+state.region.name+'.csv');
  }
})

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  // Region dropdown menu
  if (!event.target.matches('#dropbtn-region') && !event.path.includes(document.getElementById('regions-search'))) {
    var dropdown = document.getElementById("regions-menu");
    var box = document.getElementById("regions-search");
    if (dropdown.classList.contains('show')) {
      dropdown.classList.remove('show');
      box.classList.remove('show');
    }
  }

  // Graph options dropdown menus
  if (!event.path.includes(document.getElementById("filters-col")) && document.getElementById("show-filters").classList.contains("checked")) {
    let filter = d3.select("#show-filters");
    filter.classed("checked", !filter.classed("checked"));

    document.getElementById("graph-filters").classList.toggle("show");
  }

  // About popup
  if (!event.target.matches('#about-button') && !event.path.includes(document.getElementById('about-details'))) {
    var dropdown = document.getElementById("about-details");
    if (dropdown.classList.contains('show')) {
      dropdown.classList.remove('show');
    }
  }
}

const plotWidth = d3.select("#chart").node().getBoundingClientRect().width,
    plotHeight = window.innerHeight - d3.select(".header").node().getBoundingClientRect().height
                - d3.select(".filters").node().getBoundingClientRect().height
                - 2 * d3.select(".ei-border-bottom").node().getBoundingClientRect().height
                - d3.select("#chart-options").node().getBoundingClientRect().height
                - 60;

let plot = d3.select("#chart")
    .attr("width", plotWidth)
    .attr("height", plotHeight);

let tooltipDiv = d3.select("body").append("div");
let popupDiv = d3.select("body").append("div");
let timeSliderDiv = d3.select("#time-slider");

let margin = {top: 20, right: 30, bottom: 20, left: 30},
    width = plotWidth - margin.left - margin.right,
    height = plotHeight - margin.top - margin.bottom;

let svg = plot.append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

const dateParse = d3.timeParse("%Y");

let chart;

if (window.innerWidth >= 1040) loadData('./data/'+state.result.folder+'/'+state.region.name+'.csv');

function loadData(path, type='csv') {
  let loaded;
  if (type === 'csv') {
    loaded = d3.csv(path);
  } else {
    loaded = d3.json(path);
  }
  Promise.all([loaded]).then(function(data){
    let energyDemandPathway = data[0];
    // console.log(energyDemandPathway);

    let scenarios = getUniquesMenu(energyDemandPathway, 'scenario');
    state.scenario = scenarios[0];

    let selectScenario = addButtons("buttons-scenario", scenarios)
    updateSelectedButton(selectScenario, state.scenario);
    selectScenario.selectAll(".btn-ei").on("click", (event, d) => {
      if (d !== state.scenario) {
        state.scenario = d;
        chart.hideRule();
        chart.tooltip.hide();
        updateSelectedButton(selectScenario, state.scenario);
        filterData();
        getMenuOptions();
        updatePlot();
      }
    });

    state.filteredData = energyDemandPathway;
    state.rawData = energyDemandPathway;

    let secondaryMenus = state.result.columns;
    state.rawUniqueItems = {};
    state.filteredUniqueItems = {};

    secondaryMenus.forEach(sm => {
      let s = sm.name;
      state.filteredUniqueItems[s] = getUniquesMenu(state.filteredData, s);
      state.rawUniqueItems[s] = getUniquesMenu(state.rawData, s).map(d => {
        let obj = {};
        obj.name = d;
        obj.selected = state.filteredUniqueItems[sm.name].includes(d);
        return obj;
      });
    })

    updatePlot = function() {
      chart.updateData(state.dataToPlot);
      chart.updatePlot();
    }

    function getMenuOptions() {
      let graphFilters = d3.select("#graph-filters");

      let graphMenus = graphFilters.selectAll(".graph-menu")
        .data(secondaryMenus);

      graphMenus.attr("class", "graph-menu");

      graphMenus.enter().append("div")
        .attr("class", "graph-menu");

      graphMenus.exit().remove();

      let graphMenusInfo = graphFilters.selectAll(".graph-menu").selectAll(".graph-menu-info")
        .data(d => [d]);

      graphMenusInfo.attr("class", "graph-menu-info");

      graphMenusInfo.enter().append("div")
        .attr("class", "graph-menu-info");

      graphMenusInfo.exit().remove();

      let graphMenuTitle = graphFilters.selectAll(".graph-menu").selectAll(".graph-menu-info").selectAll(".graph-menu-title")
        .data(d => [d])

      graphMenuTitle.attr("class", "graph-menu-title")
        .html(d => d.longName);

      graphMenuTitle.enter().append("span")
        .attr("class", "graph-menu-title")
        .html(d => d.longName);

      graphMenuTitle.exit().remove();

      let graphMenuDetail = graphFilters.selectAll(".graph-menu").selectAll(".graph-menu-info").selectAll(".graph-menu-detail")
        .data(d => [d])

      graphMenuDetail.attr("class", "graph-menu-detail")
        .html(d => `<p>${d.description}</p>`);

      graphMenuDetail.enter().append("span")
        .attr("class", "graph-menu-detail")
        .html(d => `<p>${d.description}</p>`);

      graphMenuDetail.exit().remove();

      let graphMenuDropdown = graphFilters.selectAll(".graph-menu").selectAll(".dropdown")
        .data(d => [d.name]);

      graphMenuDropdown.attr("class", "dropdown")
        .attr("id", d => d+'-dropdown');

      graphMenuDropdown.enter().append("div")
        .attr("class", "dropdown")
        .attr("id", d => d+'-dropdown');

      graphMenuDropdown.exit().remove();

      let graphMenuDropbtn = graphFilters.selectAll(".graph-menu").selectAll(".dropdown").selectAll(".dropbtn")
        .data(d => [d]);

      graphMenuDropbtn.attr("class", "dropbtn")
        .attr("id", d => d+'-dropbtn');

      graphMenuDropbtn.enter().append("div")
        .attr("class", "dropbtn")
        .attr("id", d => d+'-dropbtn');

      graphMenuDropbtn.exit().remove();

      let graphMenuDropcontent = graphFilters.selectAll(".graph-menu").selectAll(".dropdown").selectAll(".dropdown-content")
        .data(d => [d]);

      graphMenuDropcontent.attr("class", "dropdown-content")
        .attr("id", d => d+'-menu');

      graphMenuDropcontent.enter().append("div")
        .attr("class", "dropdown-content")
        .attr("id", d => d+'-menu');

      graphMenuDropcontent.exit().remove();

      state.filteredUniqueItems = {};
      secondaryMenus.forEach(sm => {
        let s = sm.name;
        state.filteredUniqueItems[s] = getUniquesMenu(state.filteredData, s);

        let selectOption = addOptions(s+"-menu", state.rawUniqueItems[sm.name]);
        d3.select("#"+s+"-dropbtn")
          .on("click", function(event, d){
            d3.selectAll(".dropdown-content").filter(e => e !== d).classed("show", false);
            document.getElementById(s+"-menu").classList.toggle("show");
          });
        updateDropdownLabel("#"+s+"-dropdown", `${state.rawUniqueItems[s].filter(d => d.selected === true).length} selected`);
        selectOption.selectAll("span").on("click", (event, d) => {
          if (d === 'Select all') {
            state.rawUniqueItems[s].forEach(ui => ui.selected = true);
          } else if (d === 'Deselect all') {
            state.rawUniqueItems[s].forEach(ui => ui.selected = false);
          }
          chart.hideRule();
          chart.tooltip.hide();
          updateGroupByMenu();
          filterData();
          getMenuOptions();
          updatePlot();
        })
        selectOption.selectAll("a").selectAll("input").on("change", (event, d) => {
          state.rawUniqueItems[s].filter(item => item.name === d.name)[0].selected = !d.selected;
          chart.hideRule();
          chart.tooltip.hide();
          updateGroupByMenu();
          filterData();
          getMenuOptions();
          updatePlot();
          d3.select(event.target).node().parentNode.parentNode.classList.add("show");
        });
      });

      d3.select("#show-filters")
        .style("display", "block")
        .on("click", (event, d) => {
          chart.hideRule();
          chart.tooltip.hide();

          let filter = d3.select(event.target);
          filter.classed("checked", !filter.classed("checked"));

          document.getElementById("graph-filters").classList.toggle("show");
        });
    }

    function resetOptions(){
      secondaryMenus.forEach(d => {
        let menuOptions = getUniquesMenu(state.rawData, d.name);
        if (state.chart === 'area' && d.name === 'flow_category') {
          state[d.name] = menuOptions.includes('Final consumption') ? ['Final consumption'] : menuOptions;
        } else {
          state[d.name] = menuOptions;
        }
      });
      getMenuOptions()
    }

    resetOptions();

    let years = energyDemandPathway.columns.filter(d => !isNaN(+d));

    energyDemandPathway.forEach(d => {
      years.forEach(y => {
        d[y] = +d[y]
      })
    })

    state.yearsStr = years;
    state.years = years.map(d => dateParse(d));

    filterData = function(){
      state.filteredData = energyDemandPathway.filter((d, i) => {
        let filtered = secondaryMenus.map(s => state.rawUniqueItems[s.name].filter(item => item.name === d[s.name])[0].selected);
        return ((d.scenario === state.scenario) && filtered.reduce((a, b) => a && b, true))
      })
      state.dataToPlot = {};
      state.dataToPlot.lines = [];
      let uniqueGroupBy = getUniquesMenu(state.filteredData, state.groupBy.name);

      // LINE PLOT
      uniqueGroupBy.forEach(d => {
        let obj = {};
        obj.name = d;
        let thisGroup = state.filteredData.filter(s => s[state.groupBy.name] === d);
        obj.values = years.map(y => {
          let values = {};
          values.x = dateParse(y);
          values.y = thisGroup.reduce((a,b) => a + b[y], 0)
          return values;
        })
        state.dataToPlot.lines.push(obj)
      })

      // STACKED AREA
      if (state.chart === 'area') {
        const series = d3.stack()
           .keys(uniqueGroupBy)
           .value((year, key) => state.dataToPlot.lines.filter(l => l.name === key)[0].values.filter(v => v.x - year === 0)[0].y)
           .order(d3.stackOrderNone)
           .offset(null) // d3.stackOffsetExpand for normalized
           (years.map(y => dateParse(y)));

        state.dataToPlot.lines = uniqueGroupBy.map((d,i) => {
          let obj = {}
          obj.name = d;
          obj.values = series[i].map(s => {
            let val = {};
            val.y0 = s[0];
            val.y1 = s[1];
            val.x = s.data;
            return val;
          })
          return obj;
        })
      }
    }


    function updateGroupByMenu() {

      let graphFilters = d3.select("#graph-filters");

      let groupByMenus = graphFilters.selectAll(".groupby-menu")
        .data([{'name': 'Group by', 'description': "The group by filter is offered to enable visualizations that 'bundle up' output into categories defined by any one of the previous filters."}]);

      groupByMenus.attr("class", "groupby-menu");

      groupByMenus.enter().append("div")
        .attr("class", "groupby-menu");

      groupByMenus.exit().remove();

      let groupByMenuInfo = graphFilters.selectAll(".groupby-menu").selectAll(".groupby-menu-info")
        .data(d => [d])

      groupByMenuInfo.attr("class", "groupby-menu-info");

      groupByMenuInfo.enter().append("div")
        .attr("class", "groupby-menu-info");

      groupByMenuInfo.exit().remove();

      let groupByMenuTitle = graphFilters.selectAll(".groupby-menu").selectAll(".groupby-menu-info").selectAll(".groupby-menu-title")
        .data(d => [d])

      groupByMenuTitle.attr("class", "groupby-menu-title")
        .html(d => d.name);

      groupByMenuTitle.enter().append("span")
        .attr("class", "groupby-menu-title")
        .html(d => d.name);

      groupByMenuTitle.exit().remove();

      let groupByMenuDetail = graphFilters.selectAll(".groupby-menu").selectAll(".groupby-menu-info").selectAll(".groupby-menu-detail")
        .data(d => [d])

      groupByMenuDetail.attr("class", "groupby-menu-detail")
        .html(d => `<p>${d.description}</p>`);

      groupByMenuDetail.enter().append("span")
        .attr("class", "groupby-menu-detail")
        .html(d => `<p>${d.description}</p>`);

      groupByMenuDetail.exit().remove();

      let groupByMenuDropdown = graphFilters.selectAll(".groupby-menu").selectAll(".dropdown")
        .data(d => [d]);

      groupByMenuDropdown.attr("class", "dropdown")
        .attr("id", d => 'groupby-dropdown');

      groupByMenuDropdown.enter().append("div")
        .attr("class", "dropdown")
        .attr("id", d => 'groupby-dropdown');

      groupByMenuDropdown.exit().remove();

      let groupByMenuDropbtn = graphFilters.selectAll(".groupby-menu").selectAll(".dropdown").selectAll(".dropbtn")
        .data(d => [d]);

      groupByMenuDropbtn.attr("class", "dropbtn")
        .attr("id", d => 'groupby-dropbtn');

      groupByMenuDropbtn.enter().append("div")
        .attr("class", "dropbtn")
        .attr("id", d => 'groupby-dropbtn');

      groupByMenuDropbtn.exit().remove();

      let groupByMenuDropcontent = graphFilters.selectAll(".groupby-menu").selectAll(".dropdown").selectAll(".dropdown-content")
        .data(d => [d]);

      groupByMenuDropcontent.attr("class", "dropdown-content")
        .attr("id", d => 'groupby-menu');

      groupByMenuDropcontent.enter().append("div")
        .attr("class", "dropdown-content")
        .attr("id", d => 'groupby-menu');

      groupByMenuDropcontent.exit().remove();

      let groupByOptions = secondaryMenus;
      // secondaryMenus.forEach(s => {
      //   if (state[s.name] === 'All') groupByOptions.push(s)
      // })

      if (groupByOptions.length === 0) {
        d3.select(".groupby-menu")
          .style("display", "none");
      } else {
        d3.select(".groupby-menu")
          .style("display", "block");

        let groupByOps = d3.select("#groupby-menu");
        let options = groupByOps.selectAll("a").data(groupByOptions);

        options.html(d => d.longName);

        options.enter().append("a")
          .html(d => d.longName);

        options.exit().remove();

        d3.select("#groupby-dropdown")
          .on("click", function(d){
            document.getElementById("groupby-menu").classList.toggle("show");
          });
        if (state.groupBy === null) state.groupBy = groupByOptions[0];
        updateDropdownLabel("#groupby-dropdown", state.groupBy.longName);
        groupByOps.selectAll("a").on("click", (event, d) => {
          if (d !== state.groupBy) {
            state.groupBy = d;
            updateDropdownLabel("#groupby-dropdown", state.groupBy.longName);
            filterData();
            updatePlot();
          }
        });

        graphFilters.selectAll(".groupby-menu").raise();
      }
    }
    updateGroupByMenu();
    filterData();

    let yAxisUnit = state.result.name + " (" + state.result.units[0].label + ")";

    let margin = state.chart == 'treemap' ? {top: 0, right: 0, bottom: 0, left: 0} : {top: 20, right: 30, bottom: 20, left: 30},
        width = plotWidth - margin.left - margin.right,
        height = plotHeight - margin.top - margin.bottom;

    svg.attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    chart = new Chart(state.dataToPlot,
                      svg,
                      width,
                      height,
                      margin,
                      'linear',
                      popupDiv,
                      tooltipDiv,
                      timeSliderDiv,
                      yAxisUnit,
                      type=state.chart);
    chart.updatePlot();

  })
}
