/* eslint max-lines: "off" */
import qs from "querystring";

import { mount } from "enzyme";
import _ from "lodash";
import React from "react";
import { Provider } from "react-redux";
import Select from "react-select";

import { expect, it } from "@jest/globals";

import mockPopsicle from "../../MockPopsicle";
import reduxUtils from "../../redux-test-utils";
import { buildInnerHTML, clickMainMenuButton, tick, tickUpdate, withGlobalJquery } from "../../test-utils";

const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "offsetHeight");
const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "offsetWidth");
const originalInnerWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "innerWidth");
const originalInnerHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "innerHeight");

describe("DataViewer tests", () => {
  const { location, open, opener } = window;
  let result, Duplicates, Columns;

  beforeAll(() => {
    delete window.location;
    delete window.open;
    delete window.opener;
    window.location = {
      href: "http://localhost:8080/dtale/main/1",
      reload: jest.fn(),
      pathname: "/dtale/column/1",
      assign: jest.fn(),
    };
    window.open = jest.fn();
    window.opener = { code_popup: { code: "test code", title: "Test" } };
    Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
      configurable: true,
      value: 500,
    });
    Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
      configurable: true,
      value: 800,
    });
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1205,
    });
    Object.defineProperty(window, "innerHeight", {
      configurable: true,
      value: 775,
    });
    const mockBuildLibs = withGlobalJquery(() =>
      mockPopsicle.mock(url => {
        const { urlFetcher } = require("../../redux-test-utils").default;
        if (_.startsWith(url, "/dtale/duplicates")) {
          const urlParams = qs.parse(url.split("?")[1]);
          if (urlParams.action === "test") {
            return { results: { Foo: ["foo"] } };
          } else {
            return { data_id: 1 };
          }
        }
        return urlFetcher(url);
      })
    );
    const mockChartUtils = withGlobalJquery(() => (ctx, cfg) => {
      const chartCfg = { ctx, cfg, data: cfg.data, destroyed: false };
      chartCfg.destroy = () => (chartCfg.destroyed = true);
      chartCfg.getElementsAtXAxis = _evt => [{ _index: 0 }];
      chartCfg.getElementAtEvent = _evt => [{ _datasetIndex: 0, _index: 0, _chart: { config: cfg, data: cfg.data } }];
      return chartCfg;
    });
    jest.mock("popsicle", () => mockBuildLibs);
    jest.mock("chart.js", () => mockChartUtils);
    jest.mock("chartjs-plugin-zoom", () => ({}));
    jest.mock("chartjs-chart-box-and-violin-plot/build/Chart.BoxPlot.js", () => ({}));
    Duplicates = require("../../../popups/duplicates/Duplicates").ReactDuplicates;
    Columns = require("../../../popups/duplicates/Columns").Columns;
  });

  beforeEach(async () => {
    const { DataViewer } = require("../../../dtale/DataViewer");
    const store = reduxUtils.createDtaleStore();
    buildInnerHTML({ settings: "" }, store);
    result = mount(
      <Provider store={store}>
        <DataViewer />
      </Provider>,
      { attachTo: document.getElementById("content") }
    );
    await tick();
    clickMainMenuButton(result, "Duplicates");
    await tickUpdate(result);
  });

  afterAll(() => {
    window.location = location;
    window.open = open;
    window.opener = opener;
    Object.defineProperty(HTMLElement.prototype, "offsetHeight", originalOffsetHeight);
    Object.defineProperty(HTMLElement.prototype, "offsetWidth", originalOffsetWidth);
    Object.defineProperty(window, "innerWidth", originalInnerWidth);
    Object.defineProperty(window, "innerHeight", originalInnerHeight);
  });

  it("DataViewer: duplicate columns", async () => {
    result.find(Duplicates).find("div.modal-body").find("button").first().simulate("click");
    expect(result.find(Columns).length).toBe(1);
    const columnsComp = result.find(Columns).first();
    const columnsInputs = columnsComp.find(Select);
    columnsInputs.first().instance().onChange({ value: "last" });
    columnsComp.find("button").last().simulate("click");
    await tickUpdate(result);
    result.find("div.modal-footer").first().find("button").first().simulate("click");
    await tickUpdate(result);
    expect(window.location.assign).toBeCalledWith("http://localhost:8080/dtale/main/1");
  });
});
