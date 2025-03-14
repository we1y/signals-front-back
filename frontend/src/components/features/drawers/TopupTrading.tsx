'use client'

import { Button } from "@/components/ui/common/button";
import { Input } from "@/components/ui/common/input";
import { Label } from "@/components/ui/common/label";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { balanceService } from "@/services/balance.service";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";
import VirtualKeyboard from "@/components/ui/custom/VirtualKeyboard";
import failed from '../../../../public/icons/hand.png';
import Image from 'next/image';

export default function TopupTrading() {
  const [inputValue, setInputValue] = useState<string>("");
  const queryClient = useQueryClient();
  const router = useRouter();
  const [keyboard, setKeyboard] = useState<boolean>(false);

  const { data } = useQuery({
    queryKey: ['balance'],
    queryFn: () => balanceService.getUserBalance()
  })

  const t = useTranslations("TopupTradingDrawer");

  const mutation = useMutation({
    mutationKey: ['transfer to trading'],
    mutationFn: async (amount: number) => {
        try {
            const response = await balanceService.transferToTrading(amount);
            if (!response) {
                throw new Error("No response received");
            }
            return response;
        } catch (error) {
            throw error;
        }
    },
    onError: () => {
        queryClient.invalidateQueries();
        router.push(`/failed?message=${encodeURIComponent("Недостаточно средств для перевода")}`);
    },
    onSuccess: () => {
        queryClient.invalidateQueries();
        router.push(`/success?message=${encodeURIComponent("Средства успешно переведены")}`);
    }
});

  const tranferToTrading = () => {
    if (inputValue && parseFloat(inputValue) > 0) {
      mutation.mutate(parseFloat(inputValue))
    }
  }

  const handleKeyPress = (key: string) => {
    setInputValue((prev) => {
      const newValue = prev + key;
      return newValue;
    });
  };
  
  const handleDelete = () => {
    setInputValue((prev) => prev.slice(0, -1));
  };

  return (
        <div className='m-4'>
            {data?.balance !== undefined && data?.balance > 0 ? (
              <div className='space-y-4'>
                <Label className="text-black">{t("label")}</Label>
                <Input
                type="text" 
                placeholder={t("inputplaceholder")} 
                onChange={(e) => setInputValue(e.target.value)}
                onFocus={(e) => e.target.blur()}
                value={inputValue}
                readOnly
                onClick={() => setKeyboard(!keyboard)}
                />
                {keyboard ? <VirtualKeyboard onKeyPress={handleKeyPress} onDelete={handleDelete}/> : ''}
                <Button onClick={tranferToTrading} className="w-full bg-primary text-primary-foreground hover:bg-primary">{t("button")}</Button>
              </div>
            ) : (
              <div className='space-y-4 text-center font-bold flex flex-col items-center'>
                <Image src={failed} alt=""/>
                <p className="text-black">{t("nosuch")}</p>
              </div>
            )}  
        </div>
  )
}