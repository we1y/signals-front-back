import { api } from "@/api/instance.api";
import { DisableAutomodResponse, EnableAutomodResponse, User } from "@/types/user.interface";
import { getUserAuthToken } from "./auth.service";


class UserService {
    public async getUser() {
        try {
            const token = await getUserAuthToken();
            const response = await api.get<User>(`auth?token=${token}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async findUserById(telegram_id: number) {
        try {
            const response = await api.get<User>(`user/${telegram_id}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async findUserByUsername(telegram_username: string) {
        try {
            const response = await api.get<User>(`user/${telegram_username}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async setAutomodEnable() {
        try {
            const response = await api.post<EnableAutomodResponse>(`signals/enable_automode?telegram_id=${(await this.getUser()).telegram_id}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async setAutomodDisable() {
        try {
            const response = await api.post<DisableAutomodResponse>(`signals/disable_automode?telegram_id=${(await this.getUser()).telegram_id}`);
            return response;
        } catch (error) {
            throw error;
        }
    }

    public async getAutomod() {
        try {
            const response = await api.get<User>(`user/${(await this.getUser()).telegram_id}`);
            const automod = response.automod;
            return automod;
        } catch (error) {
            throw error;
        }
    }

    public async inWork() {
        try {
            const response = await api.get<User>(`user/${(await this.getUser()).telegram_id}`);
            const automod = response.in_work;
            return automod;
        } catch (error) {
            throw error;
        }
    }
}

export const userService = new UserService()