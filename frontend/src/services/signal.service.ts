import { api } from "@/api/instance.api";
import { ActiveSignals, CustomSignal, JoinSignalResponse, RandomSignal } from "@/types/signal.interface";
import { userService } from "./user.service";
import { Profits } from "@/types/signal.interface";

class SignalService {
    public async joinSignal(telegram_id: number, signal_id: number) {
        try {
            const response = await api.post<JoinSignalResponse>('signals/join', {
                telegram_id,
                signal_id
            });
    
            if (response.success) {
                return response;
            } else {
                const { message, required_amount, current_balance } = response;
                console.log(message, required_amount, current_balance)
            }
        } catch (error: any) {
            if (error.response && error.response.data) {
                const { message } = error.response.data;
                console.log(message)
            } else {
                console.log(error)
            }
        }
    }

    public async createCustomSignal(name: string, joinTime: number, activeTime: number, burnChance: number, profitPercent: number) {
        try {
            const response = await api.post<CustomSignal>('signals/create_custom', {
                "name": name,
                "join_time": joinTime,
                "active_time": activeTime,
                "burn_chance": burnChance,
                "profit_percent": profitPercent
            });
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async createRandomSignal(name: string) {
        try {
            const response = await api.post<RandomSignal>('signals/create_random', {
                "name": name
            });
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async activeSignals() {
        try {
            const response = await api.get<ActiveSignals>(`signals/active?telegram_id=${(await userService.getUser()).telegram_id}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async profits() {
            try {
                const response = await api.get<Profits>(`profits/${(await userService.getUser()).telegram_id}`);
                return response;
            } catch (error) {
                throw error;
            }
        }
}

export const signalService = new SignalService()