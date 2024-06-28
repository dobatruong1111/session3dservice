package com.saolasoft.websocket.api;

import com.saolasoft.websocket.base.response.APIResponseHeader;
import com.saolasoft.websocket.session3d.service.Session3dService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.saolasoft.websocket.session3d.dto.Session3dDtoCreate;
import com.saolasoft.websocket.session3d.dto.Session3dDtoGet;
import com.saolasoft.websocket.base.response.APIResponse;

@CrossOrigin(
		origins = {
				"http://192.168.1.172:3000"
		},
		methods = {
				RequestMethod.POST
		}
)

@RestController
public class Session3dAPI {
	
	@Autowired
	private Session3dService session3DService;

	@PostMapping("/3dlink")
    public APIResponse<Session3dDtoGet> getWebSocketUrl(@RequestBody Session3dDtoCreate object) {
		Session3dDtoGet session = session3DService.create(object);
		return new APIResponse<>(new APIResponseHeader(200, "Created"), session);
    }
}
