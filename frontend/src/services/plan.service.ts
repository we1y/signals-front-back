import { api } from "@/api/instance.api";
import { userService } from "@/services/user.service";
import { PlanResponse } from "@/types/plan.interface";
import { User } from "@/types/user.interface";

class PlanService {
    public async updateUserPlan(plan_id: number) {
        try {
            const telegram_id = (await userService.getUser()).telegram_id;
            const response = await api.put<PlanResponse>(`user/${telegram_id}/update_plan?new_plan=${plan_id}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async getUserPlan() {
        try {
            const telegram_id = (await userService.getUser()).telegram_id;
            const response = await api.get<User>(`user/${telegram_id}`);
            const userPlan = response.plan;
            return userPlan;
        } catch (error) {
            throw error;
        }
    }

}

export const planService = new PlanService()