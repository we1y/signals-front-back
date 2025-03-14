import { api } from "@/api/instance.api";
import { userService } from "@/services/user.service";
import { ReinvestResponse } from "@/types/reinvest.interface";

class ReinvestService {
    public async setUserReinvest(value: number) {
        try {
            const telegram_id = (await userService.getUser()).telegram_id;
            const response = await api.put<ReinvestResponse>(`user/${telegram_id}/update_reinvestments?new_value=${value}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

}

export const reinvestService = new ReinvestService()