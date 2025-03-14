'use client'

import { Card } from "@/components/ui/common/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/common/tabs";
import { Button } from "@/components/ui/common/button";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { planService } from "@/services/plan.service";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import premium from '../../../../public/icons/yellow.png';
import standart from '../../../../public/icons/blue.png';
import premiumplus from '../../../../public/icons/green.png';

export default function Plans() {
    const t = useTranslations("Plans");
    const router = useRouter();
    const [plan, setPlan] = useState<number>(0);
    const queryClient = useQueryClient();


    const { data } = useQuery({
      queryKey: ['user plan'],
      queryFn: () => planService.getUserPlan()
    });

    const plans = useMutation({
      mutationKey: ['update plan'],
      mutationFn: (plan_id: number) => planService.updateUserPlan(plan_id),
      onError: (error: any) => console.log(error),
      onSuccess: () => {
        queryClient.invalidateQueries();
        router.push(`/success?message=${encodeURIComponent("План успешно изменен")}`);
      }
    });


    const handleTabChange = (value: any) => {
        setPlan(parseInt(value));
    };

    return (
        <div className='space-y-4 m-4'>
              <Card className="p-2 font-bold flex justify-center">
                  {t("currentplan")}: {data === 0 ? t("standart") : 
                  data === 1 ? t("premium") : 
                  data === 2 ? t("premiumplus") : 
                  'Unknown'}
              </Card>
              <h1 className="text-black flex justify-center font-bold">{t("work")}</h1>
              <Tabs defaultValue="0" onValueChange={handleTabChange}>
                <TabsList className="grid w-full h-full grid-cols-3 bg-foreground space-x-2">
                  <TabsTrigger value="0" className="flex-col data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-primary bg-blue-100 p-2">
                    <Image src={standart} alt="" width={60} height={60}/>
                    {t("standart")}
                  </TabsTrigger>
                  <TabsTrigger value="1" className="flex-col data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-primary bg-blue-100 p-2">
                    <Image src={premium} alt="" width={60} height={60}/>
                    {t("premium")}
                  </TabsTrigger>
                  <TabsTrigger value="2" className="flex-col data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-primary bg-blue-100 p-2">
                    <Image src={premiumplus} alt="" width={60} height={60}/>
                    {t("premiumplus")}
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="0">
                    <div className='text-center p-4 space-y-2 items-start flex flex-col text-black'>
                        <div className="flex justify-between w-full">
                            <span>{t("cells")}</span>
                            <span className="text-primary font-bold">2</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("poolsignals")}</span>
                            <span className="text-primary font-bold">2</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("percentage")}</span>
                            <span className="text-primary font-bold">До 0.8%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("automodprofit")}</span>
                          <span className="text-primary font-bold">0.5%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("freezetime")}</span>
                          <span className="font-bold">14 дней</span>
                        </div>
                    </div>
                </TabsContent>
                <TabsContent value="1">
                  <div className='text-center p-4 space-y-2 items-start flex flex-col text-black'>
                        <div className="flex justify-between w-full">
                            <span>{t("cells")}</span>
                            <span className="text-primary font-bold">4</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("poolsignals")}</span>
                            <span className="text-primary font-bold">4</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("percentage")}</span>
                            <span className="text-primary font-bold">До 0.8%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("automodprofit")}</span>
                          <span className="text-primary font-bold">0.5%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("freezetime")}</span>
                          <span className="font-bold">14 дней</span>
                        </div>
                    </div>
                </TabsContent>
                <TabsContent value="2">
                    <div className='text-center p-4 space-y-2 items-start flex flex-col text-black'>
                        <div className="flex justify-between w-full">
                            <span>{t("cells")}</span>
                            <span className="text-primary font-bold">5</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("poolsignals")}</span>
                            <span className="text-primary font-bold">5</span>
                        </div>
                        <div className="flex justify-between w-full">
                            <span>{t("percentage")}</span>
                            <span className="text-primary font-bold">До 0.8%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("automodprofit")}</span>
                          <span className="text-primary font-bold">0.5%</span>
                        </div>
                        <div className="flex justify-between w-full">
                          <span>{t("freezetime")}</span>
                          <span className="font-bold">14 дней</span>
                        </div>
                    </div>
                </TabsContent>
              </Tabs>
              <p className="text-muted text-center">Нажимая кнопку "Принять", вы соглашаетесь с выбранными условиями и отменить их будет невозможно!</p>
              <Button className="bg-primary hover:bg-primary text-primary-foreground w-full" onClick={() =>  plans.mutate(plan)}>{t("accept")}</Button>
        </div>
    )
}