package com.saolasoft.websocket.base.response;

public class APIResponse<T> extends BaseAPIResponse<APIResponseHeader, T> {

    private static final long serialVersionUID = 1L;

	public APIResponse() {
        super();
    }

    public APIResponse(APIResponseHeader header, T body) {
        super(header, body);
    }
}
