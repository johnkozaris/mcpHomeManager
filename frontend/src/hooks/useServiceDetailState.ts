import { useReducer } from "react";
import type {
  GenericToolDefinition,
  ServiceDetail,
  TestResult,
} from "@/lib/types";

interface ServiceDetailState {
  editing: boolean;
  editUrl: string;
  editDisplayName: string;
  editToken: string;
  editConfig: string;
  configError: string | null;
  deleteOpen: boolean;
  importOpen: boolean;
  addToolOpen: boolean;
  appPreviewHtml: string | null;
  previewAppName: string | null;
  editToolDef: GenericToolDefinition | null;
  deleteToolName: string | null;
  testToolResults: Record<string, TestResult>;
  testingToolName: string | null;
}

type Action =
  | { type: "START_EDIT"; service: ServiceDetail }
  | { type: "CANCEL_EDIT" }
  | { type: "EDIT_SAVED" }
  | { type: "SET_EDIT_URL"; value: string }
  | { type: "SET_EDIT_DISPLAY_NAME"; value: string }
  | { type: "SET_EDIT_TOKEN"; value: string }
  | { type: "SET_EDIT_CONFIG"; value: string }
  | { type: "SET_CONFIG_ERROR"; error: string | null }
  | { type: "SET_DELETE_OPEN"; open: boolean }
  | { type: "SET_IMPORT_OPEN"; open: boolean }
  | { type: "SET_ADD_TOOL_OPEN"; open: boolean }
  | { type: "SET_APP_PREVIEW"; html: string | null; name: string | null }
  | { type: "UPDATE_APP_PREVIEW_HTML"; html: string }
  | { type: "SET_EDIT_TOOL_DEF"; tool: GenericToolDefinition | null }
  | { type: "SET_DELETE_TOOL_NAME"; name: string | null }
  | {
      type: "SET_TEST_TOOL_RESULT";
      toolName: string;
      result: TestResult;
    }
  | { type: "SET_TESTING_TOOL_NAME"; name: string | null };

const initialState: ServiceDetailState = {
  editing: false,
  editUrl: "",
  editDisplayName: "",
  editToken: "",
  editConfig: "",
  configError: null,
  deleteOpen: false,
  importOpen: false,
  addToolOpen: false,
  appPreviewHtml: null,
  previewAppName: null,
  editToolDef: null,
  deleteToolName: null,
  testToolResults: {},
  testingToolName: null,
};

function reducer(
  state: ServiceDetailState,
  action: Action,
): ServiceDetailState {
  switch (action.type) {
    case "START_EDIT":
      return {
        ...state,
        editing: true,
        editDisplayName: action.service.display_name,
        editUrl: action.service.base_url,
        editToken: "",
        editConfig: JSON.stringify(action.service.config || {}, null, 2),
        configError: null,
      };
    case "CANCEL_EDIT":
    case "EDIT_SAVED":
      return { ...state, editing: false, configError: null };
    case "SET_EDIT_URL":
      return { ...state, editUrl: action.value };
    case "SET_EDIT_DISPLAY_NAME":
      return { ...state, editDisplayName: action.value };
    case "SET_EDIT_TOKEN":
      return { ...state, editToken: action.value };
    case "SET_EDIT_CONFIG":
      return { ...state, editConfig: action.value, configError: null };
    case "SET_CONFIG_ERROR":
      return { ...state, configError: action.error };
    case "SET_DELETE_OPEN":
      return { ...state, deleteOpen: action.open };
    case "SET_IMPORT_OPEN":
      return { ...state, importOpen: action.open };
    case "SET_ADD_TOOL_OPEN":
      return { ...state, addToolOpen: action.open };
    case "SET_APP_PREVIEW":
      return {
        ...state,
        appPreviewHtml: action.html,
        previewAppName: action.name,
      };
    case "UPDATE_APP_PREVIEW_HTML":
      return { ...state, appPreviewHtml: action.html };
    case "SET_EDIT_TOOL_DEF":
      return { ...state, editToolDef: action.tool };
    case "SET_DELETE_TOOL_NAME":
      return { ...state, deleteToolName: action.name };
    case "SET_TEST_TOOL_RESULT":
      return {
        ...state,
        testToolResults: {
          ...state.testToolResults,
          [action.toolName]: action.result,
        },
      };
    case "SET_TESTING_TOOL_NAME":
      return { ...state, testingToolName: action.name };
  }
}

export function useServiceDetailState() {
  return useReducer(reducer, initialState);
}
