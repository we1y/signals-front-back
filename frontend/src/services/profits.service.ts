import { api } from "@/api/instance.api";
import { userService } from "./user.service";
import { Profits } from "@/types/profits.interface";


class ProfitsSerivce {
    public async profits() {
        try {
            const response = await api.get<Profits>(`profits/${(await userService.getUser()).telegram_id}`);
            const amount = response.amount;
            return amount;
        } catch (error) {
            throw error;
        }
    }
}

export const profitsService = new ProfitsSerivce()